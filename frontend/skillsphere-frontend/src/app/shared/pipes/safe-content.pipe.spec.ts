import { TestBed } from '@angular/core/testing';
import { DomSanitizer } from '@angular/platform-browser';
import { SafeContentPipe } from './safe-content.pipe';

describe('SafeContentPipe', () => {
  let pipe: SafeContentPipe;
  let sanitizer: DomSanitizer;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [SafeContentPipe],
    });
    sanitizer = TestBed.inject(DomSanitizer);
    pipe = TestBed.inject(SafeContentPipe);
  });

  it('should be created', () => {
    expect(pipe).toBeTruthy();
  });

  it('should handle null, undefined, and empty string safely', () => {
    expect(pipe.transform(null)).toBe('');
    expect(pipe.transform(undefined)).toBe('');
    expect(pipe.transform('')).toBe('');
    expect(pipe.transform('   ')).toBe('');
  });

  it('should parse markdown headings correctly', () => {
    const input = '# Main Title\n## Sub Title\n### Section Title';
    const output = pipe.parseMarkdown(input);
    expect(output).toContain('<h1 class="lesson-main-heading">Main Title</h1>');
    expect(output).toContain('<h2 class="lesson-heading">Sub Title</h2>');
    expect(output).toContain('<h3 class="lesson-subheading">Section Title</h3>');
  });

  it('should format bold and italic text', () => {
    const input = 'This is **bold text** and this is *italic text*.';
    const output = pipe.parseMarkdown(input);
    expect(output).toContain('<strong>bold text</strong>');
    expect(output).toContain('<em>italic text</em>');
  });

  it('should format bullet and numbered lists', () => {
    const input = '- Item one\n- Item two\n- Item three';
    const output = pipe.parseMarkdown(input);
    expect(output).toContain('<ul class="lesson-bullet-list">');
    expect(output).toContain('<li>Item one</li>');
    expect(output).toContain('<li>Item two</li>');
    expect(output).toContain('<li>Item three</li>');
    expect(output).toContain('</ul>');

    const numInput = '1. Step one\n2. Step two';
    const numOutput = pipe.parseMarkdown(numInput);
    expect(numOutput).toContain('<ol class="lesson-numbered-list">');
    expect(numOutput).toContain('<li>Step one</li>');
    expect(numOutput).toContain('<li>Step two</li>');
  });

  it('should format inline code and fenced code blocks with language tags', () => {
    const input = 'Use `npm install` to setup.\n\n```typescript\nconst message = "Hello";\n```';
    const output = pipe.parseMarkdown(input);
    expect(output).toContain('<code class="inline-code">npm install</code>');
    expect(output).toContain('code-block-wrapper');
    expect(output).toContain('<span class="code-lang-tag">typescript</span>');
    expect(output).toContain('<pre class="code-block" data-lang="typescript"><code>const message = &quot;Hello&quot;;</code></pre>');
  });

  it('should separate multiple paragraphs', () => {
    const input = 'First paragraph text.\n\nSecond paragraph text.';
    const output = pipe.parseMarkdown(input);
    expect(output).toContain('<p class="lesson-paragraph">First paragraph text.</p>');
    expect(output).toContain('<p class="lesson-paragraph">Second paragraph text.</p>');
  });

  it('should strictly sanitize raw script tags against XSS', () => {
    const malicious = '<script>alert("xss")</script>';
    const output = pipe.parseMarkdown(malicious);
    expect(output).not.toContain('<script>');
    expect(output).toContain('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;');
  });

  it('should escape malicious img onerror tags against XSS', () => {
    const malicious = '<img src="invalid.jpg" onerror="alert(\'pwned\')">';
    const output = pipe.parseMarkdown(malicious);
    expect(output).not.toContain('<img');
    expect(output).toContain('&lt;img src=&quot;invalid.jpg&quot; onerror=&quot;alert(&#39;pwned&#39;)&quot;&gt;');
  });

  it('should convert safe YouTube URLs to responsive video embeds', () => {
    const input = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
    const output = pipe.parseMarkdown(input);
    expect(output).toContain('video-embed-container');
    expect(output).toContain('https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ');
  });
});
