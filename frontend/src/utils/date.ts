export function formatDate(dateString: string | null | undefined) {
  if (!dateString) return { time: '--:--', date: 'Never' };
  
  // Ensure the date string is treated as UTC by appending 'Z' if missing
  const utcString = dateString.endsWith('Z') ? dateString : `${dateString}Z`;
  const date = new Date(utcString);
  
  return {
    time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    date: date.toLocaleDateString()
  };
}
