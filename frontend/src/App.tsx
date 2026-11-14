import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import LoginPage from './pages/LoginPage'
import SelectOfficePage from './pages/SelectOfficePage'
import MainLayout from './components/MainLayout'
import Dashboard from './pages/Dashboard'
import ClientsPage from './pages/ClientsPage'
import DossiersPage from './pages/DossiersPage'
import ProjetsPage from './pages/ProjetsPage'
import MissionsPage from './pages/MissionsPage'
import EquipePage from './pages/EquipePage'
import PartenairesPage from './pages/PartenairesPage'
import CartePage from './pages/CartePage'
import DocumentsPage from './pages/DocumentsPage'
import ParametresPage from './pages/ParametresPage'
import PlatformLayout from './pages/platform-admin/PlatformLayout'
import PlatformOverviewPage from './pages/platform-admin/PlatformOverviewPage'
import PlatformBureauxPage from './pages/platform-admin/PlatformBureauxPage'
import PlatformComingSoonPage from './pages/platform-admin/PlatformComingSoonPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div style={loadingStyle}>Chargement…</div>
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequireTenant({ children }: { children: React.ReactNode }) {
  const { activeTenant, tenants, loading } = useAuth()
  if (loading) return null
  if (tenants.length > 1 && !activeTenant) return <Navigate to="/select-office" replace />
  return <>{children}</>
}

function RequirePlatformAdmin({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div style={loadingStyle}>التحقق من الصلاحية…</div>
  if (!user) return <Navigate to="/login" replace />
  if (!user.is_platform_admin) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

function AppRoutes() {
  const { user, activeTenant, tenants, loading } = useAuth()
  if (loading) return <div style={loadingStyle}>Chargement…</div>

  return (
    <Routes>
      <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/dashboard" replace />} />
      <Route path="/select-office" element={
        <RequireAuth>
          {tenants.length > 1 && !activeTenant ? <SelectOfficePage /> : <Navigate to="/dashboard" replace />}
        </RequireAuth>
      } />
      <Route path="/" element={
        <RequireAuth>
          <RequireTenant>
            <MainLayout />
          </RequireTenant>
        </RequireAuth>
      }>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard"   element={<Dashboard />} />
        <Route path="clients"     element={<ClientsPage />} />
        <Route path="dossiers"    element={<DossiersPage />} />
        <Route path="projets"     element={<ProjetsPage />} />
        <Route path="missions"    element={<MissionsPage />} />
        <Route path="equipe"      element={<EquipePage />} />
        <Route path="partenaires" element={<PartenairesPage />} />
        <Route path="carte"       element={<CartePage />} />
        <Route path="documents"   element={<DocumentsPage />} />
        <Route path="parametres"  element={<ParametresPage />} />
      </Route>
      {/* Platform Control Center — مستقل عن اختيار المكتب (يجب أن يكون قبل مسار *) */}
      <Route path="/platform-admin/*" element={
        <RequireAuth>
          <RequirePlatformAdmin>
            <PlatformLayout />
          </RequirePlatformAdmin>
        </RequireAuth>
      }>
        <Route index element={<Navigate to="/platform-admin/overview" replace />} />
        <Route path="overview" element={<PlatformOverviewPage />} />
        <Route path="bureaux" element={<PlatformBureauxPage />} />
        <Route path="users" element={
          <PlatformComingSoonPage
            module="إدارة المستخدمين"
            description="جميع الحسابات المسجلة في المنصة، مراجعة الحالات، الروابط بالمكاتب، وصلاحيات مسير المنصة."
            status="pending-api"
          />
        } />
        <Route path="notifications" element={
          <PlatformComingSoonPage
            module="الإشعارات المركزية"
            description="استقبال إشعارات المكاتب، تصنيفها حسب النوع والأولوية، ومتابعتها حتى الإغلاق."
            status="pending-api"
          />
        } />
        <Route path="support" element={
          <PlatformComingSoonPage
            module="الدعم الفني"
            description="نظام تذاكر متكامل: إنشاء التذاكر، تعيين المسؤول، المحادثة، المرفقات، وإغلاق التذاكر."
            status="pending-api"
          />
        } />
        <Route path="communication" element={
          <PlatformComingSoonPage
            module="التواصل المركزي"
            description="إرسال إعلانات لجميع المكاتب أو لمكتب محدد، إشعارات الصيانة، التنبيهات الأمنية، والتحديثات."
            status="pending-api"
          />
        } />
        <Route path="activity" element={
          <PlatformComingSoonPage
            module="النشاط العام"
            description="مراقبة تسجيل الدخول، إنشاء المكاتب، انضمام المستخدمين، تغييرات العضويات، والأحداث المهمة."
            status="pending-api"
          />
        } />
        <Route path="security" element={
          <PlatformComingSoonPage
            module="الأمن"
            description="محاولات الدخول، محاولات الدخول الفاشلة، الأحداث الأمنية، تغييرات الصلاحيات، والتحذيرات المتعلقة بالنشاط المشبوه."
            status="pending-api"
          />
        } />
        <Route path="monitoring" element={
          <PlatformComingSoonPage
            module="مراقبة البنية التقنية"
            description="حالة Django Backend، REST APIs، PostgreSQL، PostGIS، التخزين، والأخطاء التقنية."
            status="pending-api"
          />
        } />
        <Route path="configuration" element={
          <PlatformComingSoonPage
            module="إعدادات المنصة"
            description="الإعدادات العامة، اللغات المتاحة، إعدادات الإشعارات، الميزات المفعلة، وإعدادات الصيانة."
            status="pending-api"
          />
        } />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

const loadingStyle: React.CSSProperties = {
  minHeight: '100vh', display: 'flex', alignItems: 'center',
  justifyContent: 'center', fontSize: '15px', color: '#64748b',
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
