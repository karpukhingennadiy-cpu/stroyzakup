import { LkLayoutClient } from "./lk-layout-client";

export default function LkLayout({ children }: { children: React.ReactNode }) {
  return <LkLayoutClient>{children}</LkLayoutClient>;
}
