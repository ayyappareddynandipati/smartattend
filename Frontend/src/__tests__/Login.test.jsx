import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Login from '../pages/Login';
import { useAuth } from '../context/AuthContext';

vi.mock('../context/AuthContext', () => ({ useAuth: vi.fn() }));

const renderLogin = () =>
    render(
        <MemoryRouter initialEntries={['/login']}>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/admin" element={<p>Admin dashboard</p>} />
            </Routes>
        </MemoryRouter>,
    );

const fillAndSubmit = async (username, password) => {
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/username/i), username);
    await user.type(screen.getByLabelText(/^password/i), password);
    await user.click(screen.getByRole('button', { name: /sign in/i }));
};

describe('Login page', () => {
    beforeEach(() => vi.clearAllMocks());

    it('shows an error for invalid credentials', async () => {
        const login = vi.fn().mockResolvedValue({ success: false });
        useAuth.mockReturnValue({ login, logout: vi.fn() });

        renderLogin();
        await fillAndSubmit('admin', 'wrong');

        expect(login).toHaveBeenCalledWith('admin', 'wrong');
        expect(await screen.findByText('Invalid username or password')).toBeInTheDocument();
    });

    it('navigates to the role dashboard after a successful login', async () => {
        const login = vi.fn().mockResolvedValue({ success: true, role: 'admin', first_login: false });
        useAuth.mockReturnValue({ login, logout: vi.fn() });

        renderLogin();
        await fillAndSubmit('admin', 'secret1');

        expect(await screen.findByText('Admin dashboard')).toBeInTheDocument();
    });
});
