import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString } from "openapi-typescript";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outputPath = path.resolve(__dirname, "../src/api/schema.d.ts");
const apiUrl = process.env.API_DOCS_URL || "http://localhost:8000/api/v1/docs/openapi.json";

async function generate() {
  try {
    console.log(`Fetching OpenAPI spec from: ${apiUrl}`);
    const ast = await openapiTS(apiUrl);
    const contents = astToString(ast);

    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, contents, "utf-8");
    console.log(`Generated types successfully at: ${outputPath}`);
  } catch (err) {
    if (fs.existsSync(outputPath)) {
      console.warn(`Warning: Could not fetch live OpenAPI spec (${err.message}). Using existing ${outputPath}.`);
    } else {
      console.error(`Error: Failed to fetch OpenAPI spec from ${apiUrl} and no schema.d.ts exists.`);
      console.error("Please make sure the backend server or Docker container is running.");
      process.exit(1);
    }
  }
}

generate();
