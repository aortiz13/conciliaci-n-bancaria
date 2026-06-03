import { serve } from "inngest/next";

import { inngest } from "@/lib/inngest/client";
import { functions } from "@/lib/inngest/functions";

// Endpoint que Inngest invoca para ejecutar los workflows durables.
export const { GET, POST, PUT } = serve({ client: inngest, functions });
