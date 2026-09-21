import { chromium } from "@playwright/test";

async function snap() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
  
  await page.goto("http://localhost:5173/products");
  
  // If welcome modal is visible, click 'Get Started'
  const getStartedBtn = page.locator("button:has-text('Get Started')");
  if (await getStartedBtn.isVisible()) {
    await getStartedBtn.click();
    await page.waitForTimeout(1000);
  }
  
  // Wait for product cards
  await page.waitForSelector("article, [class*='rounded-2xl']", { timeout: 10000 });
  await page.waitForTimeout(1000);
  
  // Scroll down so products are centered in view
  await page.evaluate(() => window.scrollBy(0, 450));
  await page.waitForTimeout(1000);
  
  const screenshotPath = "C:/Users/PARTH/.gemini/antigravity/brain/14b7acee-1d83-4519-bf88-e7dec8519b10/products_live.png";
  await page.screenshot({ path: screenshotPath });
  console.log("Screenshot saved to:", screenshotPath);
  
  await browser.close();
}

snap().catch(console.error);
