export function Spinner({ size = 20, color = 'var(--primary)' }: { size?: number, color?: string }) {
  return (
    <div 
      className="spinner" 
      style={{ 
        width: size, 
        height: size, 
        borderTopColor: color 
      }} 
    />
  );
}
