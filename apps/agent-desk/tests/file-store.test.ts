import { describe, expect, it } from 'vitest';
import { pathKey, samePath } from '../src/main/file-store';

describe('filesystem path comparison', () => {
  it('recognizes Windows casing and separator differences in the same destination', () => {
    const resolved = 'C:\\Users\\RunnerAdmin\\AppData\\Local\\Temp\\skills\\helper';
    const supplied = 'c:/users/runneradmin/appdata/local/temp/skills/helper/';
    expect(samePath(resolved, supplied, 'win32')).toBe(true);
    expect(pathKey(resolved, 'win32')).toBe(pathKey(supplied, 'win32'));
  });

  it('does not equate another Windows drive, sibling directory, or network share', () => {
    expect(samePath('C:\\skills\\helper', 'D:\\skills\\helper', 'win32')).toBe(false);
    expect(samePath('C:\\skills\\helper', 'C:\\outside\\helper', 'win32')).toBe(false);
    expect(samePath('\\\\server\\skills\\helper', '\\\\server\\private\\helper', 'win32')).toBe(
      false,
    );
    expect(samePath('\\\\SERVER\\Skills\\helper', '\\\\server\\skills\\helper', 'win32')).toBe(
      true,
    );
  });

  it('preserves case distinctions on POSIX filesystems', () => {
    expect(samePath('/home/berry/skills/helper', '/home/Berry/skills/helper', 'linux')).toBe(false);
    expect(
      samePath('/home/berry/skills/helper', '/home/berry/skills/../skills/helper/', 'linux'),
    ).toBe(true);
  });
});
