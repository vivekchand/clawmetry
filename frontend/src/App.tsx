import { Routes, Route } from "react-router-dom";
import HelloV2 from "./HelloV2";

// Single route for Phase-0 scaffold. Per-tab routes (trace, brain, context,
// skills, approvals, ...) land in follow-up PRs once chrome is in place.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HelloV2 />} />
      {/* SPA catch-all keeps deep links from 404ing client-side. */}
      <Route path="*" element={<HelloV2 />} />
    </Routes>
  );
}
