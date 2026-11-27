import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import PrivateRoute from '../components/PrivateRoute';
import { useAuth } from '../context/AuthContext';

vi.mock('../context/AuthContext', () => ({ useAuth: vi.fn() }));

const renderAt = (path) =>
    render(
        <MemoryRouter initialEntries={[path]}>
            <Routes>
                <Route path="/login" element={<p>Login page</p>} />
                <Route element={<PrivateRoute roles={['admin']} />}>
                    <Route path="/admin" element={<p>Admin dashboard</p>} />
                </Route>
            </Routes>
        </MemoryRouter>,
    );

const mockAuth = (overrides) =>
    useAuth.mockReturnValue({
        user: null,
        loading: false,
        hasRoleSession: () => false,
        switchRole: vi.fn(),
        ...overrides,
    });

describe('PrivateRoute', () => {
    beforeEach(() => vi.clearAllMocks());

    it('redirects to /login without a session for the required role', () => {
        mockAuth({ user: { role: 'faculty' }, hasRoleSession: (role) => role === 'faculty' });
        renderAt('/admin');
        expect(screen.getByText('Login page')).toBeInTheDocument();
    });

    it('renders the page when the user has the required role', () => {
        mockAuth({ user: { role: 'admin' }, hasRoleSession: (role) => role === 'admin' });
        renderAt('/admin');
        expect(screen.getByText('Admin dashboard')).toBeInTheDocument();
    });

    it('switches to the matching role session when another role is active', () => {
        const switchRole = vi.fn();
        mockAuth({ user: { role: 'faculty' }, hasRoleSession: () => true, switchRole });
        renderAt('/admin');
        expect(switchRole).toHaveBeenCalledWith('admin');
    });

    it('shows a loading state while auth is restoring', () => {
        mockAuth({ loading: true });
        renderAt('/admin');
        expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
});
