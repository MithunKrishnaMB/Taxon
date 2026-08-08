import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthPage } from './pages/AuthPage';
import { DashboardLayout } from './layouts/DashboardLayout';
import { DashboardPage } from './pages/DashboardPage';
import { IngestionPage } from './pages/IngestionPage';
import { ReconciliationPage } from './pages/ReconciliationPage';
import { AuditPage } from './pages/AuditPage';
import { TeamPage } from './pages/TeamPage';
import { AccountSettingsPage } from './pages/AccountSettingsPage';
import { ExportPage } from './pages/ExportPage';

function App() {
  return (
    <Routes>
      {/* PUBLIC ROUTES (Anyone can see these) */}
      <Route path="/login" element={<AuthPage />} />

      {/* PROTECTED ROUTES (Requires JWT Login) */}
      <Route element={<ProtectedRoute />}>
        {/* The Dashboard Layout will hold the Sidebar and Navbar */}
        <Route path="/" element={<DashboardLayout />}>

          {/* Default page when hitting '/' */}
          <Route index element={<DashboardPage />} />

          {/* The individual app pages */}
          <Route path="reconciliation" element={<ReconciliationPage />} />
          <Route path="ingestion" element={<IngestionPage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="export" element={<ExportPage />} />
          <Route path="team" element={<TeamPage />} />
          <Route path="settings" element={<AccountSettingsPage />} />
        </Route>
      </Route>

      {/* Catch-all for bad URLs */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;