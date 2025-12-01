'use client';

import { RoomAudioRenderer, StartAudio } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { SessionProvider } from '@/components/app/session-provider';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/livekit/toaster';
import { cn } from '@/lib/utils';

interface AppProps {
    appConfig: AppConfig;
}

// --- 🌊 OCEAN THEME EMOJIS (UPDATED) 🚢 ---
const EmojiBoat = () => <span className="text-[1.5em] md:text-[2em]">🚢</span>; 
const EmojiWave = () => <span className="text-[1.5em] md:text-[2em]">🌊</span>; 

// === STATIC ICON COMPONENT (UNMODIFIED) ===
interface StaticIconProps {
    children: React.ReactNode;
    size: string;
    top: number; 
    left: number; 
    rotate: number; 
}

const StaticIcon = ({ children, size, top, left, rotate }: StaticIconProps) => (
    <div
        className={cn(
            "absolute opacity-[0.4] pointer-events-none select-none transition-none z-0",
            size,
            // Changed color for blue theme visibility
            "text-cyan-400/50" 
        )}
        style={{
            top: `${top}%`,
            left: `${left}%`,
            transform: `rotate(${rotate}deg)`,
        }}
    >
        {children}
    </div>
);


// === FUNCTION TO GENERATE RANDOM ICONS (UPDATED) ===
const generateRandomIcons = (count: number) => {
    const icons = [];
    
    for (let i = 0; i < count; i++) {
        // Generate raw numeric values for positioning and rotation
        const top = Math.random() * 100;
        const left = Math.random() * 100;
        const rotate = Math.floor(Math.random() * 90) - 45;

        const sizeOptions = [8, 10, 12, 14, 16, 20];
        const randomSize = sizeOptions[Math.floor(Math.random() * sizeOptions.length)];
        
        // Use new ocean theme emojis
        const IconComponent = i % 2 === 0 ? EmojiBoat : EmojiWave;

        icons.push(
            <StaticIcon 
                key={i}
                top={top}
                left={left}
                rotate={rotate}
                size={`w-${randomSize} h-${randomSize}`}
            >
                <IconComponent />
            </StaticIcon>
        );
    }
    return icons;
};

// Generate icons once (150 is a good visible density)
const backgroundIcons = generateRandomIcons(150);


export function App({ appConfig }: AppProps) {
    return (
        // --- 🎨 BACKGROUND COLOR UPDATED TO BLUE GRADIENT ---
        <div className="relative h-svh w-full bg-gradient-to-t from-blue-950 to-cyan-700 text-white overflow-hidden">
            
            {/* Background Static Ocean Emojis */}
            {backgroundIcons}
            
            <SessionProvider appConfig={appConfig}>
                <main className="grid h-svh grid-cols-1 place-content-center relative z-10">
                    <ViewController />
                </main>
                <StartAudio label="Setting Sail" /> {/* Label updated */}
                <RoomAudioRenderer />
                <Toaster />
            </SessionProvider>
        </div>
    );
}