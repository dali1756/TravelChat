import { createBrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './layouts/AppShell'
import { ProtectedRoute } from './auth/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import Styleguide from './pages/_Styleguide'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/_styleguide" replace />} />
        <Route path="/_styleguide" element={<Styleguide />} />
      </Route>
    </Routes>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/_styleguide" replace /> },
      { path: '/_styleguide', element: <Styleguide /> },
    ],
  },
])
