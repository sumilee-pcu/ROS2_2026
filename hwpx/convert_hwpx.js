const fs = require('fs');
const path = require('path');

const secXml = fs.readFileSync(path.join(__dirname, 'temp_unpacked/Contents/section0.xml'), 'utf8');
const headerXml = fs.readFileSync(path.join(__dirname, 'temp_unpacked/Contents/header.xml'), 'utf8');

// Parse charPr in header
const charPrMap = {};
const charPrRegex = /<hh:charPr\s+id="(\d+)"([^>]*)>(.*?)<\/hh:charPr>/gs;
let match;
while ((match = charPrRegex.exec(headerXml)) !== null) {
    const id = match[1];
    const attrs = match[2];
    const inner = match[3];
    const bold = attrs.includes('bold="1"') || inner.includes('<hh:bold');
    const italic = attrs.includes('italic="1"') || inner.includes('<hh:italic');
    const heightMatch = attrs.match(/height="(\d+)"/);
    const height = heightMatch ? parseInt(heightMatch[1], 10) : null;
    const isCodeFont = inner.includes('latin="4"') || inner.includes('symbol="4"') || inner.includes('other="4"');

    charPrMap[id] = { bold, italic, height, isCodeFont };
}

function unescapeXml(t) {
    return t.replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&apos;/g, "'");
}

function splitTopLevelPs(xml) {
    const results = [];
    const tagRegex = /<\/?hp:p\b[^>]*>/g;
    let match;
    let depth = 0;
    let startPos = -1;

    while ((match = tagRegex.exec(xml)) !== null) {
        const tag = match[0];
        if (tag.startsWith('</')) {
            depth--;
            if (depth === 0 && startPos !== -1) {
                results.push(xml.slice(startPos, tagRegex.lastIndex));
                startPos = -1;
            }
        } else if (!tag.endsWith('/>')) {
            if (depth === 0) {
                startPos = match.index;
            }
            depth++;
        }
    }
    return results;
}

function extractRawText(pXml) {
    let tPieces = [];
    const tRegex = /<hp:t\b[^>]*>(.*?)<\/hp:t>/gs;
    let tMatch;
    while ((tMatch = tRegex.exec(pXml)) !== null) {
        let t = tMatch[1];
        t = t.replace(/<hp:tab[^>]*\/>/g, ' ... ');
        t = t.replace(/<hp:lineBreak[^>]*\/>/g, '\n');
        t = t.replace(/<[^>]+>/g, '');
        t = unescapeXml(t);
        tPieces.push(t);
    }
    return tPieces.join('');
}

function extractCodeLine(pXml) {
    let tPieces = [];
    const tRegex = /<hp:t\b[^>]*>(.*?)<\/hp:t>/gs;
    let tMatch;
    while ((tMatch = tRegex.exec(pXml)) !== null) {
        let t = tMatch[1];
        t = t.replace(/<hp:tab[^>]*\/>/g, '    ');
        t = t.replace(/<hp:lineBreak[^>]*\/>/g, '\n');
        t = t.replace(/<[^>]+>/g, '');
        t = unescapeXml(t);
        tPieces.push(t);
    }
    return tPieces.join('');
}

// Convert table to markdown
function convertTableToMarkdown(tblXml) {
    const trRegex = /<hp:tr\s*[^>]*>(.*?)<\/hp:tr>/gs;
    let trMatch;
    const rows = [];
    while ((trMatch = trRegex.exec(tblXml)) !== null) {
        const rowCells = [];
        const tcRegex = /<hp:tc\s*[^>]*>(.*?)<\/hp:tc>/gs;
        let tcMatch;
        while ((tcMatch = tcRegex.exec(trMatch[1])) !== null) {
            const cellPs = splitTopLevelPs(tcMatch[1]);
            const pTexts = cellPs.map(p => parseParagraphInline(p, true).trim()).filter(Boolean);
            let cellContent = pTexts.join('<br>').replace(/\|/g, '\\|');
            rowCells.push(cellContent);
        }
        if (rowCells.length > 0) {
            rows.push(rowCells);
        }
    }

    if (rows.length === 0) return '';
    const maxCols = Math.max(...rows.map(r => r.length));
    if (maxCols === 0) return '';

    for (const r of rows) {
        while (r.length < maxCols) r.push('');
    }

    const lines = [];
    const headerRow = rows[0];
    lines.push('| ' + headerRow.join(' | ') + ' |');
    lines.push('| ' + headerRow.map(() => ':---').join(' | ') + ' |');
    for (let i = 1; i < rows.length; i++) {
        lines.push('| ' + rows[i].join(' | ') + ' |');
    }
    return lines.join('\n');
}

// Parse runs inside a paragraph to inline markdown
function parseParagraphInline(pXml, isInsideTable = false) {
    const runRegex = /<hp:run\b([^>]*)>(.*?)<\/hp:run>/gs;
    let rMatch;
    let result = '';

    while ((rMatch = runRegex.exec(pXml)) !== null) {
        const rAttrs = rMatch[1];
        const rInner = rMatch[2];
        const charPrMatch = rAttrs.match(/charPrIDRef="(\d+)"/);
        const charPrId = charPrMatch ? charPrMatch[1] : null;
        const pr = charPrMap[charPrId] || {};

        let textPieces = [];
        const tRegex = /<hp:t\b[^>]*>(.*?)<\/hp:t>/gs;
        let tMatch;
        while ((tMatch = tRegex.exec(rInner)) !== null) {
            let t = tMatch[1];
            t = t.replace(/<hp:tab[^>]*\/>/g, '    ');
            t = t.replace(/<hp:lineBreak[^>]*\/>/g, ' ');
            t = t.replace(/<[^>]+>/g, '');
            t = unescapeXml(t);
            textPieces.push(t);
        }

        let rawText = textPieces.join('');
        if (!rawText) continue;

        if (pr.isCodeFont && !isInsideTable) {
            const trimmed = rawText.trim();
            if (trimmed) {
                const leadSpace = rawText.match(/^\s*/)[0];
                const trailSpace = rawText.match(/\s*$/)[0];
                result += `${leadSpace}\`${trimmed}\`${trailSpace}`;
            } else {
                result += rawText;
            }
        } else if (pr.bold && !isInsideTable && pr.height <= 1000) {
            const trimmed = rawText.trim();
            if (trimmed) {
                const leadSpace = rawText.match(/^\s*/)[0];
                const trailSpace = rawText.match(/\s*$/)[0];
                result += `${leadSpace}**${trimmed}**${trailSpace}`;
            } else {
                result += rawText;
            }
        } else {
            result += rawText;
        }
    }

    return result;
}

function detectCodeLanguage(codeLines) {
    const fullCode = codeLines.join('\n');
    if (/^\s*(#include|int main|void |rclcpp::|std::)/m.test(fullCode)) {
        return 'cpp';
    }
    if (/^\s*(import |from |def |class |self\.)/m.test(fullCode)) {
        return 'python';
    }
    if (/<\?xml|<package|<launch|<node|<robot/m.test(fullCode)) {
        return 'xml';
    }
    if (/cmake_minimum_required|find_package|ament_target_dependencies/m.test(fullCode)) {
        return 'cmake';
    }
    if (/^\s*(ros2|sudo|source|export|colcon|git|apt|wsl|locale|cd|mkdir|pip|echo|cp|mv|rm|chmod|ls)\b/m.test(fullCode) || /^\$\s+/.test(fullCode)) {
        return 'bash';
    }
    if (/---/.test(fullCode) && /(int64|string|bool|float64|uint32)/.test(fullCode)) {
        return 'text';
    }
    if (/[│├──└───]/.test(fullCode) || /\[\s*.*?\s*\]/.test(fullCode)) {
        return 'text';
    }
    if (codeLines.some(l => l.includes('ros2 ') || l.startsWith('sudo ') || l.startsWith('source ') || l.startsWith('export '))) {
        return 'bash';
    }
    return 'text';
}

function convertHwpxToMarkdown() {
    const topLevelPs = splitTopLevelPs(secXml);
    const mdLines = [];

    const chapterTitles = {
        image1: '# 로봇 개발자를 위한 ① ROS2 프로그래밍 첫걸음',
        image2: '# 1장. ROS2 개요와 개발 환경 구축',
        image9: '# 2장. 워크스페이스와 패키지, 빌드 시스템',
        image14: '# 3장. 토픽 — 발행/구독',
        image19: '# 4장. 서비스 — 요청/응답',
        image20: '# 5장. 액션 — 목표/피드백/결과',
        image24: '# 6장. 파라미터와 커스텀 인터페이스',
        image28: '# 7장. 런치 시스템'
    };

    let isInsideTOC = false;
    let i = 0;

    while (i < topLevelPs.length) {
        const pXml = topLevelPs[i];
        const paraPrMatch = pXml.match(/paraPrIDRef="(\d+)"/);
        const paraPr = paraPrMatch ? paraPrMatch[1] : '16';

        // Check if top-level table
        const tblMatch = pXml.match(/<hp:tbl\b[^>]*>.*?<\/hp:tbl>/s);
        if (tblMatch) {
            const tableMd = convertTableToMarkdown(tblMatch[0]);
            if (tableMd) {
                mdLines.push('');
                mdLines.push(tableMd);
                mdLines.push('');
            }
            i++;
            continue;
        }

        // Check if code block (paraPr in 18, 19, 20, 21)
        if (['18', '19', '20', '21'].includes(paraPr)) {
            const codeLines = [];
            while (i < topLevelPs.length) {
                const curP = topLevelPs[i];
                const curParaPrMatch = curP.match(/paraPrIDRef="(\d+)"/);
                const curParaPr = curParaPrMatch ? curParaPrMatch[1] : '';
                if (!['18', '19', '20', '21'].includes(curParaPr)) {
                    break;
                }
                const rawLine = extractCodeLine(curP);
                codeLines.push(rawLine);
                i++;
            }

            const lang = detectCodeLanguage(codeLines);
            mdLines.push('');
            mdLines.push('```' + lang);
            mdLines.push(codeLines.join('\n'));
            mdLines.push('```');
            mdLines.push('');
            continue;
        }

        // Check if picture
        const picMatch = pXml.match(/<hp:pic\b[^>]*>.*?<\/hp:pic>/s);
        if (picMatch) {
            const imgRefMatch = picMatch[0].match(/binaryItemIDRef="([^"]+)"/);
            const imgRef = imgRefMatch ? imgRefMatch[1] : '';
            if (chapterTitles[imgRef]) {
                if (isInsideTOC) isInsideTOC = false;
                mdLines.push('');
                mdLines.push('---');
                mdLines.push('');
                mdLines.push(chapterTitles[imgRef]);
                mdLines.push('');
            }
            i++;
            continue;
        }

        const firstRunCharPrMatch = pXml.match(/<hp:run\b[^>]*charPrIDRef="(\d+)"/);
        const firstCharPr = firstRunCharPrMatch ? firstRunCharPrMatch[1] : '0';
        const rawText = extractRawText(pXml).trim();

        if (!rawText) {
            i++;
            continue;
        }

        const inlineMd = parseParagraphInline(pXml).trim();

        // Check TOC Start
        if (rawText === '차례') {
            isInsideTOC = true;
            mdLines.push('');
            mdLines.push('## CONTENT');
            mdLines.push('');
            i++;
            continue;
        }

        // Handle TOC content
        if (isInsideTOC && paraPr === '23') {
            if (/^[12]부\./.test(rawText)) {
                const partName = rawText.replace(/^([12])부\.\s*/, '제$1부 ');
                mdLines.push('');
                mdLines.push(`### ${partName}`);
                mdLines.push('');
            } else if (/^\d+장\./.test(rawText)) {
                const chapName = rawText.replace(/^(\d+)장\.\s*/, '제$1장 ');
                mdLines.push(`* **${chapName}**`);
            } else if (/^\d+\.\d+/.test(rawText)) {
                mdLines.push(`  * ${rawText}`);
            } else if (rawText.startsWith('참고문헌')) {
                mdLines.push(`* **${rawText}**`);
            } else {
                mdLines.push(`* ${rawText}`);
            }
            i++;
            continue;
        }

        // Metadata (paraPr === '17')
        if (paraPr === '17') {
            const cleanText = rawText.replace(/\s*\|\s*|\s*｜\s*/, ' | ');
            const parts = cleanText.split(' | ');
            if (parts.length === 2) {
                const label = parts[0].replace(/\s+/g, '');
                mdLines.push(`**${label}** | ${parts[1]}  `);
            } else {
                mdLines.push(rawText + '  ');
            }
            i++;
            continue;
        }

        // Caption (paraPr === '24')
        if (paraPr === '24') {
            mdLines.push('');
            mdLines.push(inlineMd);
            mdLines.push('');
            i++;
            continue;
        }

        // Forewords (머리말)
        if (rawText === '머리말') {
            mdLines.push('');
            mdLines.push('## 머리말');
            mdLines.push('');
            i++;
            continue;
        }

        if (rawText === '참고문헌') {
            mdLines.push('');
            mdLines.push('---');
            mdLines.push('');
            mdLines.push('## 참고문헌');
            mdLines.push('');
            i++;
            continue;
        }

        // Section Headers (e.g. 1.1 로봇 소프트웨어와 ROS, 2.3 [따라하기] ...)
        if (/^\d+\.\d+(\.\d+)?\b/.test(rawText)) {
            const level = (rawText.match(/\./g) || []).length;
            const prefix = level >= 2 ? '###' : '##';
            mdLines.push('');
            mdLines.push(`${prefix} ${rawText}`);
            mdLines.push('');
            i++;
            continue;
        }

        // Major Section / Subsection Titles
        if (firstCharPr === '9' || firstCharPr === '10' || firstCharPr === '15') {
            if (rawText === '이 장에서 다루는 내용' || rawText === '학습 목표' || rawText === '정리' || rawText === '핵심 용어' || rawText === '연습문제' || rawText === '연습문제 해설' || rawText.startsWith('트러블슈팅') || rawText.startsWith('공식 문서') || rawText.startsWith('커뮤니티') || rawText.startsWith('관련 도서') || rawText.startsWith('ROS1과 ROS2') || rawText.startsWith('DDS')) {
                mdLines.push('');
                mdLines.push(`### ${rawText}`);
                mdLines.push('');
                i++;
                continue;
            }
        }

        // Subheadings inside sections (all bold, short, no sentence ending)
        const runs = [...pXml.matchAll(/<hp:run\b[^>]*charPrIDRef="(\d+)"/g)].map(m => m[1]);
        const allBold = runs.length > 0 && runs.every(c => ['5', '8'].includes(c));
        if (allBold && rawText.length < 60 && !/[.!?]$/.test(rawText) && !rawText.startsWith('•') && !rawText.startsWith('*') && !/^\d+\./.test(rawText) && !rawText.startsWith('정의(')) {
            mdLines.push('');
            mdLines.push(`### ${rawText}`);
            mdLines.push('');
            i++;
            continue;
        }

        // Definitions: 정의(X) ...
        if (/^정의\(\d+\)/.test(rawText)) {
            mdLines.push('');
            mdLines.push(`> **${rawText}**  `);
            if (i + 1 < topLevelPs.length) {
                const nextP = topLevelPs[i + 1];
                const nextText = extractRawText(nextP).trim();
                const nextInline = parseParagraphInline(nextP).trim();
                const nextParaPrMatch = nextP.match(/paraPrIDRef="(\d+)"/);
                const nextParaPr = nextParaPrMatch ? nextParaPrMatch[1] : '';
                if (nextParaPr === '16' && !/^\d+\.\d+|^(이 장에서|학습 목표|정리|연습문제|정의)/.test(nextText) && !nextText.startsWith('•')) {
                    mdLines.push(`> ${nextInline}`);
                    i++;
                }
            }
            mdLines.push('');
            i++;
            continue;
        }

        // Bullet points (• or ·)
        if (rawText.startsWith('• ') || rawText.startsWith('· ')) {
            const content = inlineMd.replace(/^[•·]\s*/, '');
            mdLines.push(`* ${content}`);
            i++;
            continue;
        }

        // Numbered list items
        if (/^\d+\.\s+/.test(rawText) && rawText.length > 3) {
            mdLines.push(inlineMd);
            i++;
            continue;
        }

        // Default paragraph
        mdLines.push(inlineMd);
        mdLines.push('');
        i++;
    }

    // Clean up multiple consecutive empty lines
    let finalMd = mdLines.join('\n');
    finalMd = finalMd.replace(/\n{3,}/g, '\n\n');
    return finalMd.trim() + '\n';
}

const md = convertHwpxToMarkdown();
const targetFile = 'D:/git/ROS2_2026/hwpx/ROS2첫걸음1_B5_통합본_1-7장.md';
fs.writeFileSync(targetFile, md, 'utf8');
console.log(`Successfully written ${md.length} characters to ${targetFile}`);
