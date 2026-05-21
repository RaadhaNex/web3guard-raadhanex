import { AdminOpsHub } from "@/components/admin/AdminOpsHub";

export const metadata = {
  title: "Admin OS | Web3Guard AI",
  description: "Separated admin, monitoring, worker, provider, QA, revenue, and reviewer workspace for RAADHANEX operations.",
  robots: {
    index: false,
    follow: false,
  },
};

export default function AdminPage() {
  return <AdminOpsHub />;
}
