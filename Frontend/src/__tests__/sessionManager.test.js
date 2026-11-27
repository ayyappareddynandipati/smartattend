import { describe, expect, it } from 'vitest';
import { getRoleFromPath, getStoredSessions, isTokenExpired, SESSION_STORAGE_KEY } from '../utils/sessionManager';

const makeToken = (expSecondsFromNow) => {
    const payload = btoa(JSON.stringify({ sub: 'user', exp: Math.floor(Date.now() / 1000) + expSecondsFromNow }));
    return `header.${payload}.signature`;
};

describe('isTokenExpired', () => {
    it('is false for a token that expires in the future', () => {
        expect(isTokenExpired(makeToken(3600))).toBe(false);
    });

    it('is true for an expired token', () => {
        expect(isTokenExpired(makeToken(-10))).toBe(true);
    });

    it('treats malformed tokens as expired', () => {
        expect(isTokenExpired('not-a-jwt')).toBe(true);
    });
});

describe('getRoleFromPath', () => {
    it('maps dashboard paths to roles', () => {
        expect(getRoleFromPath('/admin')).toBe('admin');
        expect(getRoleFromPath('/faculty/session')).toBe('faculty');
        expect(getRoleFromPath('/student')).toBe('student');
        expect(getRoleFromPath('/login')).toBeNull();
    });
});

describe('getStoredSessions', () => {
    it('keeps valid sessions and drops expired or incomplete ones', () => {
        localStorage.setItem(
            SESSION_STORAGE_KEY,
            JSON.stringify({
                admin: { token: makeToken(3600), username: 'admin', first_login: 0 },
                faculty: { token: makeToken(-60), username: 'teacher' },
                student: { username: 'no-token' },
            }),
        );

        const sessions = getStoredSessions();

        expect(Object.keys(sessions)).toEqual(['admin']);
        expect(sessions.admin).toMatchObject({ username: 'admin', role: 'admin', first_login: false });
        expect(JSON.parse(localStorage.getItem(SESSION_STORAGE_KEY))).toEqual(sessions);
    });

    it('returns an empty object for corrupted storage', () => {
        localStorage.setItem(SESSION_STORAGE_KEY, '{broken');
        expect(getStoredSessions()).toEqual({});
    });
});
