import type { Metadata } from "next";
import { WorkspaceApp } from "@/components/workspace/workspace";

export const metadata: Metadata = { title: "Workspace" };

export default function WorkspacePage() {
  return <WorkspaceApp />;
}
