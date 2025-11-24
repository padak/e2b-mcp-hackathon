import { Sandbox } from "@e2b/code-interpreter";

// Backend sandbox URL cache
let backendUrl: string | null = null;
let backendSandbox: Sandbox | null = null;

const E2B_TEMPLATE = "sim-zpicena-gateway";
const BACKEND_PORT = 8000;
const GITHUB_REPO = "https://github.com/padak/e2b-mcp-hackathon.git";

/**
 * Get or create the backend sandbox URL.
 * The backend runs FastAPI and exposes HTTPS URL.
 */
export async function getBackendUrl(): Promise<string> {
  if (backendUrl && backendSandbox) {
    // Check if sandbox is still alive
    try {
      const response = await fetch(`${backendUrl}/health`, {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });
      if (response.ok) {
        return backendUrl;
      }
    } catch {
      // Sandbox is dead, recreate
      backendUrl = null;
      backendSandbox = null;
    }
  }

  // Create new sandbox
  console.log("Creating E2B backend sandbox...");

  const apiKey = process.env.E2B_API_KEY;
  if (!apiKey) {
    throw new Error("E2B_API_KEY not configured");
  }

  // Required environment variables
  const anthropicKey = process.env.ANTHROPIC_API_KEY;
  const perplexityKey = process.env.PERPLEXITY_API_KEY;

  if (!anthropicKey) {
    throw new Error("ANTHROPIC_API_KEY not configured");
  }
  if (!perplexityKey) {
    throw new Error("PERPLEXITY_API_KEY not configured");
  }

  backendSandbox = await Sandbox.create(E2B_TEMPLATE, {
    apiKey,
    timeoutMs: 600000, // 10 minutes for long simulations
  });

  try {
    // Clone the repository
    console.log("Cloning repository...");
    const cloneResult = await backendSandbox.commands.run(
      `git clone ${GITHUB_REPO} /home/user/app`,
      { timeoutMs: 60000 }
    );
    if (cloneResult.exitCode !== 0) {
      throw new Error(`Failed to clone repo: ${cloneResult.stderr}`);
    }

    // Install dependencies
    console.log("Installing dependencies...");
    try {
      await backendSandbox.commands.run(
        "cd /home/user/app && pip install -r requirements.txt fastapi uvicorn python-dotenv 2>&1",
        { timeoutMs: 180000 }
      );
      console.log("Dependencies installed successfully");
    } catch (pipError) {
      console.error("Pip install failed:", pipError);
      // Try installing core dependencies only
      console.log("Retrying with core dependencies only...");
      try {
        await backendSandbox.commands.run(
          "pip install fastapi uvicorn python-dotenv anthropic e2b-code-interpreter mesa numpy pandas plotly httpx pydantic rich mcp",
          { timeoutMs: 180000 }
        );
        console.log("Core dependencies installed");
      } catch (coreError) {
        console.error("Core install also failed:", coreError);
        throw new Error("Failed to install dependencies in E2B sandbox");
      }
    }

    // Create .env file with API keys
    console.log("Configuring environment...");
    const envContent = `
ANTHROPIC_API_KEY=${anthropicKey}
ANTHROPIC_MODEL=${process.env.ANTHROPIC_MODEL || "claude-sonnet-4-20250514"}
E2B_API_KEY=${apiKey}
PERPLEXITY_API_KEY=${perplexityKey}
`;
    await backendSandbox.files.write("/home/user/app/.env", envContent);

    // Start the backend server
    console.log("Starting FastAPI backend...");
    backendSandbox.commands.run(
      "cd /home/user/app && python -m uvicorn src.backend.api:app --host 0.0.0.0 --port 8000",
      { background: true }
    );

    // Wait for server to start
    console.log("Waiting for server to start...");
    let serverReady = false;
    const host = backendSandbox.getHost(BACKEND_PORT);
    const testUrl = `https://${host}/health`;

    for (let i = 0; i < 30; i++) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      try {
        const res = await fetch(testUrl, { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
          serverReady = true;
          break;
        }
      } catch {
        // Server not ready yet
      }
    }

    if (!serverReady) {
      throw new Error("Backend server failed to start within 30 seconds");
    }

    backendUrl = `https://${host}`;
    console.log(`Backend URL: ${backendUrl}`);

    return backendUrl;
  } catch (error) {
    // Cleanup on error
    if (backendSandbox) {
      await backendSandbox.kill();
      backendSandbox = null;
    }
    throw error;
  }
}

/**
 * Forward request to E2B backend.
 */
export async function forwardToBackend(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = await getBackendUrl();
  return fetch(`${url}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
}

/**
 * Cleanup backend sandbox.
 */
export async function cleanupBackend(): Promise<void> {
  if (backendSandbox) {
    await backendSandbox.kill();
    backendSandbox = null;
    backendUrl = null;
  }
}
