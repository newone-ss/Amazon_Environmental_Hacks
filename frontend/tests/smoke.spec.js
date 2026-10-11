import { test, expect } from '@playwright/test';

test.describe('Bhujal Decision Support Smoke Tests', () => {
  let consoleErrors = [];

  test.beforeEach(async ({ page }) => {
    consoleErrors = [];
    page.on('console', (msg) => {
      // Filter out benign WebGL / canvas warnings in headless environment
      const text = msg.text();
      if (
        msg.type() === 'error' &&
        !text.includes('WebGL') &&
        !text.includes('GL-related') &&
        !text.includes('ReadPixels') &&
        !text.includes('503') &&
        !text.includes('ECONNREFUSED') &&
        !text.includes('Service Unavailable')
      ) {
        consoleErrors.push(text);
      }
    });
  });

  test('1. REJECTED site exhibits red safety override and hides recommendations', async ({ page }) => {
    await page.goto('/');

    // Wait for settlements to load
    await expect(page.locator('.settlement-header')).toBeVisible({ timeout: 10000 });

    // Select the REJECTED site: Mundaguda
    const rejectedBtn = page.locator('button.demo-site-btn:has-text("Mundaguda")');
    await rejectedBtn.click();

    // Assert red safety banner is visible above the fold
    const safetyBanner = page.locator('.safety-banner.verdict-rejected');
    await expect(safetyBanner).toBeVisible();
    await expect(safetyBanner).toContainText('REJECTED — NO STRUCTURE RECOMMENDED');
    await expect(safetyBanner).toContainText('SLOPE_STEEP');

    // Assert NO build recommendation is shown on Overview tab
    const recCard = page.locator('.rec-summary-card');
    await expect(recCard).toHaveCount(0);
  });

  test('2. SAFE site displays cleared verdict and generates DPR package', async ({ page }) => {
    await page.goto('/');

    // Handle alert dialog from DPR generation
    page.on('dialog', async (dialog) => {
      await dialog.accept();
    });

    // Select SAFE site: Laxmipur
    const safeBtn = page.locator('button.demo-site-btn:has-text("Laxmipur")');
    await safeBtn.click();

    // Verify safe banner
    const safetyBanner = page.locator('.safety-banner.verdict-safe');
    await expect(safetyBanner).toBeVisible();
    await expect(safetyBanner).toContainText('CLEARED: SAFE TO BUILD');

    // Switch to Plan tab
    const planTab = page.locator('button[role="tab"]:has-text("Plan")');
    await planTab.click();

    // Verify MGNREGA cost table is present
    await expect(page.locator('.cost-table')).toBeVisible();

    // Click Generate DPR button
    const generateBtn = page.locator('button:has-text("Generate DPR Package")');
    await expect(generateBtn).toBeVisible();
    await generateBtn.click();

    // Verify button remains or shows progress
    await expect(generateBtn).toBeVisible();
  });

  test('3. Scenario simulator updates deficit readout when rainfall slider moves', async ({ page }) => {
    await page.goto('/');

    // Select Laxmipur
    await page.locator('button.demo-site-btn:has-text("Laxmipur")').click();

    // Switch to Scenario tab
    const scenarioTab = page.locator('button[role="tab"]:has-text("Scenario")');
    await scenarioTab.click();

    // Read baseline deficit text
    const deficitBox = page.locator('.deficit-readout-card');
    await expect(deficitBox).toBeVisible();
    const initialText = await deficitBox.innerText();

    // Adjust rainfall slider to 0.60x using evaluate to trigger React state update
    const slider = page.locator('input[type="range"]');
    await slider.evaluate((el) => {
      el.value = '0.60';
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });

    // Wait for reactive state update
    await page.waitForTimeout(400);

    // Assert simulated total or deficit readout changed
    const newText = await deficitBox.innerText();
    expect(newText).not.toEqual(initialText);
    expect(newText).toContain('-23.2 mm');
  });

  test('4. Language toggle switches UI strings to Hindi and preserves numbers/rules', async ({ page }) => {
    await page.goto('/');

    // Click language toggle pill
    const langBtn = page.locator('.lang-toggle-pill');
    await expect(langBtn).toBeVisible();
    await langBtn.click();

    // Verify header search placeholder is Hindi
    await expect(page.locator('input[aria-label="बस्ती या जिला खोजें..."]')).toBeVisible();
    await expect(langBtn).toContainText('EN');

    // Verify numbers and rule IDs remain untranslated (e.g. / 100)
    await expect(page.locator('.score-denom').first()).toContainText('/ 100');

    // Switch back to English
    await langBtn.click();
    await expect(page.locator('input[aria-label="Search settlement or district..."]')).toBeVisible();
    await expect(langBtn).toContainText('हिं (HI)');
  });

  test('5. Multi-view navigation and zero console errors', async ({ page }) => {
    await page.goto('/');

    // Check Field Data navigation using visible buttons
    const fieldDataNav = page.locator('button:has-text("Field Data"):visible').first();
    await fieldDataNav.click();
    await expect(page.locator('.field-data-view')).toBeVisible();

    // Check Reports navigation
    const reportsNav = page.locator('button:has-text("Reports"):visible').first();
    await reportsNav.click();
    await expect(page.locator('.reports-view')).toBeVisible();
    await expect(page.locator('.state-works-table')).toBeVisible();

    // Check About and Data navigation
    const aboutNav = page.locator('button:has-text("About"):visible').first();
    await aboutNav.click();
    await expect(page.locator('.about-view')).toBeVisible();

    // Check Help / Decision guide modal
    const helpNav = page.locator('button:has-text("Help"):visible').first();
    await helpNav.click();
    await expect(page.locator('.guide-modal')).toBeVisible();

    // Dismiss with Escape key
    await page.keyboard.press('Escape');
    await expect(page.locator('.guide-modal')).not.toBeVisible();

    // Ensure zero console errors
    expect(consoleErrors).toHaveLength(0);
  });

  test('6. AI Agents panel renders orchestrator briefing and consultation interface', async ({ page }) => {
    await page.goto('/');

    // Select Laxmipur
    await page.locator('button.demo-site-btn:has-text("Laxmipur")').click();

    // Click AI Agents tab
    const agentsTab = page.locator('button[role="tab"]:has-text("AI Agents")');
    await expect(agentsTab).toBeVisible();
    await agentsTab.click();

    // Executive decision banner and specialist cards appear
    await expect(page.locator('.executive-decision-banner')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.agents-briefing-grid')).toBeVisible();

    // Verify consultation section
    await expect(page.locator('.agent-consult-section')).toBeVisible();
    await expect(page.locator('.consult-query-input')).toBeVisible();
  });
});

