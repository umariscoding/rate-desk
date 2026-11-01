// Run with the API in AGENT_MODE=replay (free) or record. Needs Chrome and the app on :5173.
// End-to-end walk through Rate Desk in a real browser: salesperson -> DORM (messy reply) -> automatic correction
// email -> DORM (clean reply) -> salesperson builds and downloads the proposal.
import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";

const OUT = path.resolve("e2e/out"); // Screenshots and the downloaded proposal land here.
fs.mkdirSync(OUT, { recursive: true });
const URL = "http://localhost:5173/";
const SLOW = 180_000; // agent steps can take a while on a first, live run

const browser = await chromium.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true,
});
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
const page = await context.newPage();
const problems = [];
page.on("pageerror", (error) => problems.push(`page error: ${error.message}`));
page.on("response", (response) => response.status() >= 400 && problems.push(`HTTP ${response.status()} ${response.request().method()} ${response.url().replace("http://localhost:5173", "")}`));
page.on("console", (message) => false);

let stepNumber = 0;
async function step(name, action) {
  stepNumber += 1;
  const label = `${String(stepNumber).padStart(2, "0")} ${name}`;
  try {
    await action();
    console.log(`PASS ${label}`);
  } catch (error) {
    await page.screenshot({ path: path.join(OUT, `FAIL-${String(stepNumber).padStart(2, "0")}.png`), fullPage: true });
    console.log(`FAIL ${label}\n     ${String(error.message).split("\n")[0]}`);
    console.log(`     screenshot: e2e/out/FAIL-${String(stepNumber).padStart(2, "0")}.png`);
    if (problems.length) console.log("     browser problems:", problems.slice(-3));
    await browser.close();
    process.exit(1);
  }
}
const shot = (name) => page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: true });

async function signIn(fullName) {
  await page.goto(URL);
  await page.getByRole("row", { name: new RegExp(fullName) }).getByRole("button", { name: "Fill in" }).click();
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.locator(".appbar__user").getByText(fullName).waitFor();
}
const signOut = async () => {
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.getByRole("heading", { name: "Sign in" }).waitFor();
};
const lastMessageFrame = () => page.frameLocator("iframe.mail__body").last();

// ── Salesperson submits and approves ────────────────────────────────────────
await step("login page shows both demo accounts", async () => {
  await page.goto(URL);
  await page.getByText("Umar Azhar").waitFor();
  await page.getByText("DORM A").waitFor();
});
await step("wrong password is refused with a clear message", async () => {
  await page.getByLabel("Username").fill("umar");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByText("The username or password is not right").waitFor();
});
await step("salesperson signs in and sees an empty inbox", async () => {
  await signIn("Umar Azhar");
  await page.getByText("Nothing needs you right now").waitFor();
  await page.getByText("No requests yet").waitFor();
  await shot("01-sales-empty-inbox");
});
await step("new request: paste the sample email and read it (agents)", async () => {
  await page.locator(".appbar__tab", { hasText: "New request" }).click();
  await page.getByRole("button", { name: "Complete request" }).click();
  await page.getByRole("button", { name: "Read email", exact: true }).click();
  await page.getByRole("button", { name: /Approve and send to the DORM/ }).waitFor({ timeout: SLOW });
});
await step("case record: client, rooms board and next step are right", async () => {
  await page.getByRole("heading", { name: "Company A", level: 2 }).waitFor();
  await page.getByText("Client A").first().waitFor();
  await page.getByText("Your next step:").waitFor();
  await page.getByText("Review the rate request and send it to the DORM").first().waitFor();
  for (const forbidden of ["Priya", "Daniel", "DOM "]) {
    if ((await page.content()).includes(forbidden)) throw new Error(`found forbidden text: ${forbidden}`);
  }
  await shot("02-sales-case-drafted");
});
await step("salesperson approves the rate request", async () => {
  await page.getByRole("button", { name: /Approve and send to the DORM/ }).click();
  await page.getByText("Waiting for the DORM to reply").first().waitFor();
});
await step("salesperson signs out", signOut);

// ── DORM replies (messy), gets an automatic correction email ────────────────
await step("DORM signs in: inbox shows one request needing a reply", async () => {
  await signIn("DORM A");
  await page.getByText("1 waiting for your reply").waitFor();
  await page.getByText("Reply needed").waitFor();
  await shot("03-dorm-inbox");
});
await step("DORM cannot reach the salesperson's data", async () => {
  const status = await page.evaluate(async () => {
    const token = JSON.parse(localStorage.getItem("rate-desk-session")).token;
    const response = await fetch("/api/v1/cases", { headers: { Authorization: `Bearer ${token}` } });
    return response.status;
  });
  if (status !== 403) throw new Error(`expected 403, got ${status}`);
});
await step("DORM opens the request and clicks Reply all", async () => {
  await page.getByRole("button", { name: /rate request/i }).first().click();
  await page.getByRole("button", { name: "Reply all" }).click();
  await page.locator("#reply-editor iframe").waitFor();
});
await step("messy sample fills the yellow cells; the DORM can also type", async () => {
  await page.getByRole("button", { name: "Fill in a messy reply" }).click();
  const editor = page.frameLocator("#reply-editor iframe");
  const cells = editor.locator("td.rate");
  if ((await cells.first().innerText()).trim() !== "129") throw new Error("first rate cell is not 129");
  await cells.first().click();
  await page.keyboard.press("Tab"); // moves to the next rate cell, not out of the email
  await page.keyboard.type("0");
  const second = (await cells.nth(1).innerText()).trim();
  if (!second.endsWith("0")) throw new Error(`Tab+type did not reach the second cell: "${second}"`);
  await shot("04-dorm-reply-editor");
});
await step("DORM sends; the correction email arrives automatically (agents)", async () => {
  await page.getByRole("button", { name: "Send reply" }).click();
  await page.locator("h3", { hasText: "Message from the sales desk" }).nth(1).waitFor({ timeout: SLOW });
  await lastMessageFrame().getByText("What we still need from you").waitFor();
  await shot("05-dorm-correction-email");
});
await step("correction grid: yellow cells to fill, green cells already given", async () => {
  const frame = lastMessageFrame();
  const yellow = await frame.locator("td.rate").count();
  const green = await frame.locator("td.ok").count();
  if (yellow < 3 || green < 1) throw new Error(`expected yellow>=3 and green>=1, got ${yellow}/${green}`);
});

// ── DORM answers once with the clean reply ──────────────────────────────────
await step("DORM replies once with a clean reply (agents)", async () => {
  await page.getByRole("button", { name: "Reply all" }).click();
  await page.locator("#reply-editor iframe").waitFor();
  await page.getByRole("button", { name: "Fill in a clean reply" }).click();
  await page.getByRole("button", { name: "Send reply" }).click();
  await page.getByText("You have replied. The sales desk will write back").waitFor({ timeout: SLOW });
  await shot("06-dorm-done");
});
await step("DORM signs out", signOut);

// ── Salesperson builds the proposal ─────────────────────────────────────────
await step("salesperson inbox: rates confirmed, next step is the proposal", async () => {
  await signIn("Umar Azhar");
  await page.getByText("1 need your action").waitFor();
  await page.getByText("Rates confirmed").first().waitFor();
  await page.getByText("Build the proposal").first().waitFor();
  await shot("07-sales-inbox-confirmed");
});
await step("case shows exact totals and no open problems", async () => {
  await page.getByRole("button", { name: "Company A" }).click();
  // 28,730 while the hotel policy is not in the knowledge base; 31,130 once the Rate Guard has corrected Friday's low rate.
  await page.getByText(/€(28,730|31,130)\.00/).first().waitFor();
  if (await page.getByText("to fix before this can become a proposal").count()) throw new Error("problems still listed");
  await shot("08-sales-rate-check");
});
await step("build the proposal, get the cover email, download it", async () => {
  await page.getByRole("button", { name: "Build the proposal" }).click();
  await page.getByRole("button", { name: "Download proposal" }).waitFor({ timeout: SLOW });
  await page.getByText("Checked against the quote").waitFor();
  await page.getByText("Cover email for the client").waitFor({ timeout: SLOW });
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Download proposal" }).click(),
  ]);
  const target = path.join(OUT, "proposal.docx");
  await download.saveAs(target);
  if (fs.statSync(target).size < 10_000) throw new Error("downloaded proposal is too small");
  await shot("09-sales-proposal-ready");
});
await step("salesperson sees agent activity and cost", async () => {
  await page.getByText("Agent activity").waitFor();
});

console.log(problems.length ? `\nbrowser problems (${problems.length}):\n${problems.join("\n")}` : "\nno browser errors");
await browser.close();
console.log(`\nALL ${stepNumber} STEPS PASSED`);
