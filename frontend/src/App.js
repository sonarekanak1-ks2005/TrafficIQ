import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { TrafficProvider } from '@/contexts/TrafficContext';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopBar } from '@/components/layout/TopBar';
import { Toaster } from '@/components/ui/sonner';
import Dashboard from '@/pages/Dashboard';
import Prediction from '@/pages/Prediction';
import RoutesPage from '@/pages/Routes';
import Analytics from '@/pages/Analytics';
import AlertsPage from '@/pages/Alerts';
import Weather from '@/pages/Weather';

function App() {
    return (
        <BrowserRouter>
            <TrafficProvider>
                <div className="app-root tiq-app-bg">
                    <Sidebar />
                    <div className="app-main">
                        <TopBar />
                        <main className="content-wrap">
                            <Routes>
                                <Route path="/" element={<Dashboard />} />
                                <Route path="/prediction" element={<Prediction />} />
                                <Route path="/routes" element={<RoutesPage />} />
                                <Route path="/weather" element={<Weather />} />
                                <Route path="/analytics" element={<Analytics />} />
                                <Route path="/alerts" element={<AlertsPage />} />
                                <Route path="*" element={<Navigate to="/" replace />} />
                            </Routes>
                        </main>
                    </div>
                </div>
                <Toaster richColors position="top-right" theme="dark" />
            </TrafficProvider>
        </BrowserRouter>
    );
}

export default App;
