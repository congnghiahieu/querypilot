import { useEffect, useRef, useState } from 'react';

interface TypewriterTextProps {
  text: string;
  onComplete?: () => void;
  speed?: number;
}

const TypewriterText = ({ text, onComplete, speed = 20 }: TypewriterTextProps) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (currentIndex < text.length) {
      intervalRef.current = setTimeout(() => {
        setDisplayText((prev) => prev + text[currentIndex]);
        setCurrentIndex((prev) => prev + 1);
      }, speed);
    } else if (onComplete) {
      onComplete();
    }

    return () => {
      if (intervalRef.current) {
        clearTimeout(intervalRef.current);
      }
    };
  }, [currentIndex, text, onComplete, speed]);

  useEffect(() => {
    setDisplayText('');
    setCurrentIndex(0);
  }, [text]);

  return <span>{displayText}</span>;
};

export default TypewriterText;
