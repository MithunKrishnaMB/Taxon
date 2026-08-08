import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';

function App() {
  return (
    <Routes>
      {/* PUBLIC ROUTES (Anyone can see these) */}
      <Route path="/login" element={<div className="p-10 text-2xl font-bold">Login Page (Stitch goes here)</div>} />

      {/* PROTECTED ROUTES (Requires JWT Login) */}
      <Route element={<ProtectedRoute />}>
        {/* The Dashboard Layout will hold the Sidebar and Navbar */}
        <Route path="/" element={<div className="p-10 text-2xl font-bold text-blue-600">Dashboard Layout (Stitch goes here)</div>}>

          {/* Default page when hitting '/' */}
          <Route index element={<Navigate to="/reconciliation" replace />} />

          {/* The individual app pages */}
          <Route path="reconciliation" element={<div>Auto-IMS Reconciliation Page</div>} />
          <Route path="ingestion" element={<div>Bulk File Upload Page</div>} />
          <Route path="audit" element={<div>Statutory Audit Trail Page</div>} />
        </Route>
      </Route>

      {/* Catch-all for bad URLs */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;