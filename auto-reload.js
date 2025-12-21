const puppeteer = require("puppeteer");
const chokidar = require("chokidar");
const path = require("path");

class ExtensionAutoReloader {
  constructor(extensionPath) {
    this.extensionPath = path.resolve(extensionPath);
    this.browser = null;
    this.extensionId = null;
  }

  async start() {
    this.browser = await puppeteer.launch({
      headless: false,
      args: [
        `--disable-extensions-except=${this.extensionPath}`,
        `--load-extension=${this.extensionPath}`,
        "--no-sandbox",
      ],
    });

    console.log("✓ Browser launched with extension");

    await this.getExtensionId();

    this.watchFiles();
  }

  async getExtensionId() {
    const page = await this.browser.newPage();
    await page.goto("chrome://extensions");

    this.extensionId = await page.evaluate(() => {
      const ext = document
        .querySelector("extensions-manager")
        ?.shadowRoot?.querySelector("extensions-item-list")
        ?.shadowRoot?.querySelector("extensions-item");
      return ext?.getAttribute("id");
    });

    await page.close();
    console.log(`✓ Extension ID: ${this.extensionId}`);
  }

  async reloadExtension() {
    console.log("\n🔄 Reloading extension...");

    const page = await this.browser.newPage();
    await page.goto("chrome://extensions");

    // Click reload button
    await page.evaluate((extId) => {
      const extensions = document
        .querySelector("extensions-manager")
        ?.shadowRoot?.querySelector("extensions-item-list")
        ?.shadowRoot?.querySelectorAll("extensions-item");

      for (const ext of extensions) {
        if (ext.getAttribute("id") === extId) {
          const reloadBtn = ext.shadowRoot.querySelector("#dev-reload-button");
          if (reloadBtn) reloadBtn.click();
          break;
        }
      }
    }, this.extensionId);

    await page.close();

    console.log("✓ Extension reloaded");
  }

  watchFiles() {
    const watcher = chokidar.watch(this.extensionPath, {
      ignored: /(^|[\/\\])\../,
      persistent: true,
      ignoreInitial: true,
    });

    let timeout;

    watcher.on("all", (event, filePath) => {
      console.log(`📝 File ${event}: ${path.basename(filePath)}`);

      clearTimeout(timeout);
      timeout = setTimeout(() => {
        this.reloadExtension();
      }, 500);
    });

    console.log(`\n👀 Watching for changes in: ${this.extensionPath}\n`);
  }
}

const extensionPath = "./polymarket"; // Change to your extension path

const reloader = new ExtensionAutoReloader(extensionPath);
reloader.start().catch(console.error);

process.on("SIGINT", () => {
  console.log("\n\nStopping auto-reloader...");
  process.exit();
});
