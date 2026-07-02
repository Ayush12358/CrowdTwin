import React, { createContext, useContext, useState, useEffect } from 'react';

type Theme = 'light' | 'dark';
type Accent = { h: number; s: string; l: string };

interface ThemeContextType {
    theme: Theme;
    setTheme: (t: Theme) => void;
    accent: Accent;
    setAccent: (a: Accent) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [theme, setTheme] = useState<Theme>('dark');
    const [accent, setAccent] = useState<Accent>({ h: 210, s: '100%', l: '50%' });

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        document.documentElement.style.setProperty('--accent-h', accent.h.toString());
        document.documentElement.style.setProperty('--accent-s', accent.s);
        document.documentElement.style.setProperty('--accent-l', accent.l);
    }, [theme, accent]);

    return (
        <ThemeContext.Provider value={{ theme, setTheme, accent, setAccent }}>
            {children}
        </ThemeContext.Provider>
    );
};

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
};
