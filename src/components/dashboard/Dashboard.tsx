import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { ExecutiveOverview } from "./ExecutiveOverview";

const Dashboard = () => {
  return (
    <div className="min-h-screen flex w-full bg-background text-foreground">
      <Sidebar />
      <main className="flex-1 min-w-0 flex flex-col">
        <Topbar />
        <div className="flex-1 overflow-y-auto">
          <ExecutiveOverview />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;