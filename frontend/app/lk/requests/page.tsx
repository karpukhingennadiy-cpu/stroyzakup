import { Suspense } from "react";
import { RequestsList } from "./requests-list";
import { RequestsSkeleton } from "./requests-skeleton";

export default function RequestsPage() {
  return (
    <Suspense fallback={<RequestsSkeleton />}>
      <RequestsList />
    </Suspense>
  );
}
