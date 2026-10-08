import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'safeContent',
  standalone: true,
})
export class SafeContentPipe implements PipeTransform {
  private sanitizer = inject(DomSanitizer);

  transform(value: string | null | undefined): SafeHtml | string {
    if (!value || typeof value !== 'string' || !value.trim()) {
      return '';
    }

    const formattedHtml = this.parseMarkdown(value);
    return this.sanitizer.bypassSecurityTrustHtml(formattedHtml);
  }

  private escapeHtml(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  parseMarkdown(rawText: string): string {
    const trimmed = rawText.trim();
    if (!trimmed) {
      return '';
    }

    // Step 1: Escape all raw HTML entities first to guarantee XSS safety
    let text = this.escapeHtml(rawText);

    // Step 2: Extract and stash fenced code blocks with placeholders
    const codeBlocks: string[] = [];
    text = text.replace(/```([a-zA-Z0-9_\-\.]*)\n?([\s\S]*?)```/g, (_match, lang, code) => {
      const cleanLang = (lang || 'code').trim();
      const trimmedCode = code.trim();
      const placeholder = `___SKILLSPHERE_CODE_BLOCK_${codeBlocks.length}___`;
      const htmlBlock = `<div class="code-block-wrapper"><div class="code-block-header"><span class="code-lang-tag">${cleanLang}</span></div><pre class="code-block" data-lang="${cleanLang}"><code>${trimmedCode}</code></pre></div>`;
      codeBlocks.push(htmlBlock);
      return placeholder;
    });

    // Step 3: Extract and stash embedded video URLs inside the text
    const videoBlocks: string[] = [];
    text = text.replace(
      /(?:^|\n)(https?:\/\/(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/|vimeo\.com\/)[a-zA-Z0-9_\-\?&=]+)(?:\n|$)/g,
      (_match, url) => {
        const embed = this.extractVideoEmbed(url);
        if (embed) {
          const placeholder = `\n___SKILLSPHERE_VIDEO_${videoBlocks.length}___\n`;
          videoBlocks.push(embed);
          return placeholder;
        }
        return url;
      }
    );

    // Step 4: Parse lines into structured blocks (headings, lists, paragraphs)
    const lines = text.split('\n');
    const resultBlocks: string[] = [];
    let currentList: { type: 'ul' | 'ol'; items: string[] } | null = null;
    let currentParagraph: string[] = [];

    const flushList = () => {
      if (currentList) {
        const tag = currentList.type;
        const itemsHtml = currentList.items
          .map((item) => `<li>${this.formatInline(item)}</li>`)
          .join('');
        resultBlocks.push(
          `<${tag} class="lesson-${tag === 'ul' ? 'bullet' : 'numbered'}-list">${itemsHtml}</${tag}>`
        );
        currentList = null;
      }
    };

    const flushParagraph = () => {
      if (currentParagraph.length > 0) {
        const pContent = currentParagraph.join(' ').trim();
        if (pContent) {
          resultBlocks.push(`<p class="lesson-paragraph">${this.formatInline(pContent)}</p>`);
        }
        currentParagraph = [];
      }
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmedLine = line.trim();

      // Check code block or video placeholder
      if (
        trimmedLine.startsWith('___SKILLSPHERE_CODE_BLOCK_') ||
        trimmedLine.startsWith('___SKILLSPHERE_VIDEO_')
      ) {
        flushParagraph();
        flushList();
        resultBlocks.push(trimmedLine);
        continue;
      }

      // Blank line -> separates paragraphs / lists
      if (trimmedLine === '') {
        flushParagraph();
        flushList();
        continue;
      }

      // Headings
      const h3Match = line.match(/^###\s+(.+)$/);
      const h2Match = line.match(/^##\s+(.+)$/);
      const h1Match = line.match(/^#\s+(.+)$/);

      if (h1Match || h2Match || h3Match) {
        flushParagraph();
        flushList();
        if (h3Match) {
          resultBlocks.push(`<h3 class="lesson-subheading">${this.formatInline(h3Match[1].trim())}</h3>`);
        } else if (h2Match) {
          resultBlocks.push(`<h2 class="lesson-heading">${this.formatInline(h2Match[1].trim())}</h2>`);
        } else if (h1Match) {
          resultBlocks.push(`<h1 class="lesson-main-heading">${this.formatInline(h1Match[1].trim())}</h1>`);
        }
        continue;
      }

      // Unordered lists (- or *)
      const ulMatch = line.match(/^[\*\-]\s+(.+)$/);
      if (ulMatch) {
        flushParagraph();
        if (!currentList || currentList.type !== 'ul') {
          flushList();
          currentList = { type: 'ul', items: [] };
        }
        currentList.items.push(ulMatch[1].trim());
        continue;
      }

      // Ordered lists (1., 2., etc.)
      const olMatch = line.match(/^\d+\.\s+(.+)$/);
      if (olMatch) {
        flushParagraph();
        if (!currentList || currentList.type !== 'ol') {
          flushList();
          currentList = { type: 'ol', items: [] };
        }
        currentList.items.push(olMatch[1].trim());
        continue;
      }

      // Normal text inside paragraph
      flushList();
      currentParagraph.push(trimmedLine);
    }

    flushParagraph();
    flushList();

    let output = resultBlocks.join('\n');

    // Step 5: Restore code blocks
    codeBlocks.forEach((block, idx) => {
      output = output.replace(`___SKILLSPHERE_CODE_BLOCK_${idx}___`, block);
    });

    // Step 6: Restore video blocks
    videoBlocks.forEach((embed, idx) => {
      output = output.replace(`___SKILLSPHERE_VIDEO_${idx}___`, embed);
    });

    return output;
  }

  private formatInline(text: string): string {
    // Inline code: `code`
    let formatted = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    // Bold: **text**
    formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // Italic: *text* (excluding already formatted strong)
    formatted = formatted.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');
    return formatted;
  }

  private extractVideoEmbed(url: string): string | null {
    // YouTube
    const ytMatch = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_\-]{11})/);
    if (ytMatch && ytMatch[1]) {
      const videoId = encodeURIComponent(ytMatch[1]);
      return `<div class="video-embed-container"><iframe src="https://www.youtube-nocookie.com/embed/${videoId}" title="Lesson Video Player" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>`;
    }

    // Vimeo
    const vimeoMatch = url.match(/(?:vimeo\.com\/)(\d+)/);
    if (vimeoMatch && vimeoMatch[1]) {
      const vimeoId = encodeURIComponent(vimeoMatch[1]);
      return `<div class="video-embed-container"><iframe src="https://player.vimeo.com/video/${vimeoId}" title="Lesson Video Player" loading="lazy" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe></div>`;
    }

    return null;
  }
}
