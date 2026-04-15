import { useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router";
import { useThemeStore } from "./stores/themeStore";
import { useAuthStore } from "./stores/authStore";
import { PageLayout } from "./components/layout/PageLayout";
import { HomePage } from "./pages/HomePage";
import { HotelDetailPage } from "./pages/HotelDetailPage";
import { BookingConfirmPage } from "./pages/BookingConfirmPage";
import { MyBookingsPage } from "./pages/MyBookingsPage";
import { ProfilePage } from "./pages/ProfilePage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { AdminLayout } from "./components/layout/AdminLayout";
import { HotelsAdmin } from "./pages/admin/HotelsAdmin";
import { RoomsAdmin } from "./pages/admin/RoomsAdmin";
import { ImagesAdmin } from "./pages/admin/ImagesAdmin";
import { FacilitiesAdmin } from "./pages/admin/FacilitiesAdmin";
import { NotFoundPage } from "./pages/NotFoundPage";
import { ConfirmPage } from "./pages/ConfirmPage";
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage";
import { ErrorBoundary } from "./components/ErrorBoundary";

export function App() {
  const theme = useThemeStore((s) => s.theme);
  const fetchMe = useAuthStore((s) => s.fetchMe);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          {/* Auth pages — fullscreen, no header/footer */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/confirm" element={<ConfirmPage />} />
          <Route path="/oauth/callback" element={<OAuthCallbackPage />} />

          {/* Main app — with Header + Footer */}
          <Route
            path="/*"
            element={
              <PageLayout>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/hotels/:hotelId" element={<HotelDetailPage />} />
                  <Route path="/hotels/:hotelId/book/:roomId" element={<BookingConfirmPage />} />
                  <Route path="/bookings" element={<MyBookingsPage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/admin" element={<AdminLayout />}>
                    <Route path="hotels" element={<HotelsAdmin />} />
                    <Route path="hotels/:hotelId/rooms" element={<RoomsAdmin />} />
                    <Route path="hotels/:hotelId/images" element={<ImagesAdmin />} />
                    <Route path="facilities" element={<FacilitiesAdmin />} />
                  </Route>
                  <Route path="*" element={<NotFoundPage />} />
                </Routes>
              </PageLayout>
            }
          />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
