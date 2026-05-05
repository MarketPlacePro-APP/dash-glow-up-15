import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Dashboard from "./components/dashboard/Dashboard";
import Index from "./pages/Index.tsx";
import Marketing from "./pages/Marketing.tsx";
import Preview from "./pages/Preview.tsx";
import Workshop from "./pages/Workshop.tsx";
import Schedule from "./pages/Schedule.tsx";
import InsideSales from "./pages/InsideSales.tsx";
import DataQA from "./pages/DataQA.tsx";
import NotFound from "./pages/NotFound.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route element={<Dashboard />}>
            <Route path="/" element={<Index />} />
            <Route path="/marketing" element={<Marketing />} />
            <Route path="/preview" element={<Preview />} />
            <Route path="/workshop" element={<Workshop />} />
            <Route path="/schedule" element={<Schedule />} />
            <Route path="/inside-sales" element={<InsideSales />} />
            <Route path="/data-qa" element={<DataQA />} />
          </Route>
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
