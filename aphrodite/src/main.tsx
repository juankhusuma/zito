import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import '@mantine/core/styles.css';

import { BrowserRouter, Routes, Route } from "react-router";
import { AuthProvider } from './hoc/AuthProvider.tsx';
import Login from './pages/auth/Login.tsx';
import Register from './pages/auth/Register.tsx';
import Session from './pages/chat/Session.tsx';
import Home from './pages/index.tsx';
import Navbar from './components/layout/navbar.tsx';
import Footer from './components/layout/footer.tsx';
import { MantineProvider } from '@mantine/core';
import ChatLayout from './components/chat/layout.tsx';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <MantineProvider>
        <div className='flex flex-col justify-between min-h-svh'>
          <Navbar />
          <div className='pt-5 flex-1'>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/chat" element={<ChatLayout />}>
                  <Route index element={<Session />} />
                  <Route path=":sessionId" element={<Session />} />
                </Route>
                <Route path="/chat/:sessionId" element={<Session />} />
              </Routes>
            </BrowserRouter>
          </div>
          <Footer />
        </div>
      </MantineProvider>
    </AuthProvider>
  </StrictMode>,
)
