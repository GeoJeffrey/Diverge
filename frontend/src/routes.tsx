import { createBrowserRouter, Navigate } from "react-router";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Layout from "./pages/Layout";
import TickersPage from "./pages/Tickers";
import TickerAdvanced from "./pages/TickerAdvanced";
import TickerSimple from "./pages/TickerSimple";
import IndicesPage from "./pages/Indices";
import IntegrityPage from "./pages/Integrity";
import ExplainabilityPage from "./pages/Explainability";
import Settings from "./pages/Settings";
import { ProtectedRoute } from "./components/ProtectedRoute";

export const router = createBrowserRouter([
  { path: "/", Component: Landing },
  { path: "/login", Component: Login },
  {
    Component: Layout,
    children: [
      { path: "tickers", Component: TickersPage },
      { path: "ticker/:symbol", Component: TickerAdvanced },
      { path: "ticker/:symbol/simple", Component: TickerSimple },
      { path: "indices", Component: IndicesPage },
      { path: "integrity", Component: IntegrityPage },
      { path: "explainability", Component: ExplainabilityPage },
      {
        path: "settings",
        element: (
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        ),
      },
      { path: "dashboard", element: <Navigate to="/tickers" replace /> },
    ],
  },
]);
