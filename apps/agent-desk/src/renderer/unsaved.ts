import { useEffect } from 'react';

const unsaved = new Set<string>();
export function hasUnsavedChanges(): boolean {
  return unsaved.size > 0;
}
export function useUnsavedChanges(key: string, dirty: boolean, preserveOnUnmount = false): void {
  useEffect(() => {
    if (dirty) unsaved.add(key);
    else unsaved.delete(key);
  }, [key, dirty]);
  useEffect(
    () => () => {
      if (!preserveOnUnmount) unsaved.delete(key);
    },
    [key, preserveOnUnmount],
  );
}
