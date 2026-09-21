import { chromium } from "@playwright/test";

async function testPagination() {
  console.log("Starting pagination click test on http://localhost:5173/products");
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });

  await page.goto("http://localhost:5173/products");

  // Dismiss modal if open
  const getStartedBtn = page.locator("button:has-text('Get Started')");
  if (await getStartedBtn.isVisible()) {
    await getStartedBtn.click();
    await page.waitForTimeout(500);
  }

  await page.waitForSelector("article, [class*='rounded-2xl']", { timeout: 10000 });

  // Check initial page text
  const initialPageText = await page.locator("text=/Page 1 of/").first().innerText();
  console.log("Initial state:", initialPageText);

  // Find Next button
  const nextBtn = page.locator("button:has-text('Next')");
  console.log("Is Next button visible & enabled?:", await nextBtn.isVisible(), await nextBtn.isEnabled());

  // Click Next
  console.log("Clicking Next button...");
  await nextBtn.click();
  await page.waitForTimeout(1500);

  // Check URL and page text after click
  console.log("Current URL:", page.url());
  const updatedPageText = await page.locator("text=/Page 2 of/").first().innerText();
  console.log("Updated state after click:", updatedPageText);

  if (page.url().includes("page=2") && updatedPageText.includes("Page 2 of")) {
    console.log("SUCCESS! Pagination button works perfectly and navigated to Page 2!");
  } else {
    console.error("FAILURE! Did not navigate to Page 2.");
    process.exit(1);
  }

  // Scroll to pagination buttons and take screenshot
  await page.evaluate(() => window.scrollBy(0, 800));
  await page.waitForTimeout(500);
  const snapPath = "C:/Users/PARTH/.gemini/antigravity/brain/14b7acee-1d83-4519-bf88-e7dec8519b10/pagination_verified.png";
  await page.screenshot({ path: snapPath });
  console.log("Screenshot saved to:", snapPath);

  await browser.close();
}

testPagination().catch(err => {
  console.error("Test failed:", err);
  process.exit(1);
});
