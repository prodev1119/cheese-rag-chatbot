import asyncio
import json, os
import nest_asyncio
from pyppeteer import launch
from urllib.parse import urlparse, parse_qs, unquote, urljoin

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
nest_asyncio.apply()# ADJUST THIS PATH!

class Scraper(object):
    browser = None
    products = []

    def __init__(self, url = "https://shop.kimelo.com/department/cheese/3365"):
        self.url = url
        parse = urlparse(url)
        self.baseUrl = parse[0] + "://" + parse[1] + "/"
        self.num_pages = 0

    async def scrape(self):
        self.browser = await launch(executablePath=os.environ["CHROME_PATH"])
        await self.scrapeProducts()
        await self.scrapPriceOrder()
        await self.scrapPorpularityOrder()
        await self.browser.close()

        prods = list(self.products.values())
        self.products = prods

        print(f"Successfully scrap database from '{self.url}', count: {len(prods)}")

    async def scrapeProducts(self):
        self.products = {}

        ## Open page
        page = await self.browser.newPage()
        await page.goto(self.url)

        num_pages = await page.querySelector("b.chakra-text.text-nowrap.css-itvw0n")
        num_pages = await num_pages.getProperty("textContent")
        num_pages = await num_pages.jsonValue()
        self.num_pages = int(num_pages.split("of ")[-1])

        for i in range(self.num_pages ):
            page = await self.browser.newPage()
            await page.goto(self.url + "?page=" + str(i + 1))

            ## Get product hrefs
            prods = await page.querySelectorAll("a.chakra-card.group.css-5pmr4x")

            ## Fill products
            for prod in prods:
                href = await prod.getProperty("href")
                href = await href.jsonValue()
                sku = href.split("/")[-1]

                discount = await prod.querySelector("span.chakra-text.css-87ralv")
                if discount is not None:
                    discount = await discount.getProperty("textContent")
                    discount = await discount.jsonValue()
                else:
                    discount = ""

                empty = await prod.querySelector("span.chakra-badge.css-qrs5r8")
                if empty is not None:
                    empty = True
                else:
                    empty = False

                info = await self.getProductInfo(prod, href)
                info["sku"] = sku
                info["discount"] = discount
                info["empty"] = empty
                info['href'] = urljoin(self.baseUrl, href)

                self.products[sku] = info

        self.save(os.environ.get("SCRAP_JSON", "g:\\Work\\cheese-rag-chatbot\\data\\cheese_raw.json"))

    async def scrapPriceOrder(self):
        order = 1

        for i in range(self.num_pages ):
            page = await self.browser.newPage()
            await page.goto(self.url + "?sort=price_i+desc&page=" + str(i + 1))

            ## Get product hrefs
            prods = await page.querySelectorAll("a.chakra-card.group.css-5pmr4x")

            ## Fill products
            for prod in prods:
                href = await prod.getProperty("href")
                href = await href.jsonValue()
                sku = href.split("/")[-1]

                if sku not in self.products.keys():
                    print(f"{sku} not in database")

                self.products[sku]["priceOrder"] = order
                order += 1

    async def scrapPorpularityOrder(self):
        order = 1

        for i in range(self.num_pages ):
            page = await self.browser.newPage()
            await page.goto(self.url + "?sort=popularity_i+desc&page=" + str(i + 1))

            ## Get product hrefs
            prods = await page.querySelectorAll("a.chakra-card.group.css-5pmr4x")

            ## Fill products
            for prod in prods:
                href = await prod.getProperty("href")
                href = await href.jsonValue()
                sku = href.split("/")[-1]

                if sku not in self.products.keys():
                    print(f"{sku} not in database")

                self.products[sku]["porpularityOrder"] = order
                order += 1

    async def getProductInfo(self, prod, href):
        info = {}

        ## Get showImage
        showImage = await prod.querySelector("img")
        showImage = await showImage.getProperty("srcset")
        showImage = await showImage.jsonValue()
        showImage = parse_qs(urlparse(showImage.split(" ")[0]).query)
        info["showImage"] = unquote(showImage['url'][0])

        ## Goto href
        page = await self.browser.newPage()
        await page.goto(urljoin(self.baseUrl, href))

        #  Get name
        name = await page.querySelector("h1.chakra-heading.css-18j379d")
        name = await name.getProperty("textContent")
        info["name"] = await name.jsonValue()

        #  Get brand
        name = await page.querySelector("p.chakra-text.css-drbcjm")
        name = await name.getProperty("textContent")
        info["brand"] = await name.jsonValue()

        #  Get department
        department = (await page.querySelectorAll("a.chakra-link.chakra-breadcrumb__link.css-1vtk5s8"))[1]
        department = await department.getProperty("textContent")
        info["department"] = await department.jsonValue()

        # Get table
        table_data_as_dict = await page.evaluate(
            '''(tableSelector) => {
                const table = document.querySelector(tableSelector);
                if (!table) return null;

                const headers = Array.from(table.querySelectorAll('thead tr th, thead tr td, tr:first-child th, tr:first-child td'))
                                     .map(header => header.innerText.trim());
                const dataRows = [];
                const bodyRows = table.querySelectorAll('tbody tr'); // Prioritize tbody if it exists

                const rowsToProcess = bodyRows.length > 0 ? bodyRows : table.querySelectorAll('tr:not(:has(th)):not(:first-child)');
                // Fallback if no tbody and first row wasn't headers, or if headers are complex

                Array.from(rowsToProcess).forEach(row => {
                    const cells = Array.from(row.querySelectorAll('td'));
                    let rowData = {};
                    cells.forEach((cell, index) => {
                        if (headers[index]) {
                            rowData[headers[index]] = cell.innerText.trim();
                        } else {
                            rowData[`column_${index + 1}`] = cell.innerText.trim(); // Fallback column name
                        }
                    });
                    if (Object.keys(rowData).length > 0) { // Only add if rowData is not empty
                       dataRows.push(rowData);
                    }
                });
                return dataRows;
            }''',
            "table.chakra-table.css-5605sr" # Pass the table_selector as an argument to the JS function
        )
        info["itemCounts"] = table_data_as_dict[0]
        info["dimensions"] = table_data_as_dict[1]
        info["weights"] = table_data_as_dict[2]

        #  Get images
        imageButtons = await page.querySelectorAll("button.chakra-tabs__tab.border.css-2jmkdc")
        images = []
        for ib in imageButtons:
            image = await ib.querySelector("img")
            image = await image.getProperty("srcset")
            image = await image.jsonValue()
            image = parse_qs(urlparse(image.split(" ")[0]).query)
            images.append(unquote(image['url'][0]))
        info["images"] = images

        # Related
        relatedContainer = await page.querySelector("div.css-1811skr")
        relatedLinks = await relatedContainer.querySelectorAll("a.chakra-card.group.css-5pmr4x")
        relateds = []
        for rl in relatedLinks:
            rl = await rl.getProperty("href")
            rl = await rl.jsonValue()
            relateds.append(rl.split("/")[-1])
        info["relateds"] = relateds

        # Prices
        priceContainers = await page.querySelectorAll("div.chakra-form-control.css-1kxonj9")
        prices = {}
        for pc in priceContainers[1:]:
            ts = await pc.querySelectorAll("b.chakra-text.css-0")
            ts = [await (await t.getProperty("textContent")).jsonValue() for t in ts]
            prices[ts[0]] = ts[1][1:]
        info["prices"] = prices

        # Price Per Unit
        pricePer = await priceContainers[1].querySelector("span.chakra-badge.css-1mwp5d1")
        if pricePer is None:
            pricePer = 0
        else:
            pricePer = await pricePer.getProperty("textContent")
            pricePer = await pricePer.jsonValue()
        info["pricePer"] = pricePer

        return info

    def save(self, filename):
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(self.products, json_file, indent=4, ensure_ascii=False, sort_keys=False)

        print(f"Successfully saved database to '{filename}' in a beautiful format.")

    def clear(self):
        self.products = []
        self.num_pages = 0

    def setUrl(self, url):
        self.url = url
        parse = urlparse(url)
        self.baseUrl = parse[0] + "://" + parse[1] + "/"


if __name__ == "__main__":
    scraper = Scraper()

    asyncio.run(scraper.scrape())
    scraper.save(os.environ.get("SCRAP_JSON", "g:\\Work\\cheese-rag-chatbot\\data\\cheese_raw.json"))
    print(len(scraper.products))