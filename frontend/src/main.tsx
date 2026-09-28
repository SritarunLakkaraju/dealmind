import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ToastProvider } from "./components/ui";
import "./index.css";
import DealRoom from "./pages/DealRoom";
import Pipeline from "./pages/Pipeline";
import Playbook from "./pages/Playbook";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ToastProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Pipeline />} />
            <Route path="/deals/:id" element={<DealRoom />} />
            <Route path="/playbook" element={<Playbook />} />
          </Routes>
        </Layout>
      </ToastProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
