---
name: Supervision List
description: A fair, field-matched supervision list, set like a newspaper allocation supplement.
colors:
  paper: "oklch(91.5% 0.012 95)"
  paper-raised: "oklch(95.5% 0.008 95)"
  paper-sunk: "oklch(87% 0.014 95)"
  ink: "oklch(19% 0.01 80)"
  ink-secondary: "oklch(38% 0.012 80)"
  ink-muted: "oklch(52% 0.012 80)"
  rule: "oklch(30% 0.012 80)"
  rule-soft: "oklch(76% 0.012 90)"
  press-green: "oklch(38% 0.08 160)"
  press-green-deep: "oklch(30% 0.07 160)"
  on-green: "oklch(97% 0.01 95)"
  biro: "oklch(45% 0.2 268)"
  biro-wash: "oklch(86% 0.06 268)"
  error: "oklch(42% 0.15 28)"
typography:
  masthead:
    fontFamily: "Libre Franklin, Franklin Gothic Medium, Arial Narrow, sans-serif"
    fontSize: "clamp(2.6rem, 8.5vw, 6rem)"
    fontWeight: 900
    lineHeight: 0.92
    letterSpacing: "-0.035em"
  heading:
    fontFamily: "Libre Franklin, Franklin Gothic Medium, Arial Narrow, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  label:
    fontFamily: "Libre Franklin, Franklin Gothic Medium, Arial Narrow, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Spectral, Iowan Old Style, Palatino Linotype, serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  none: "0"
  sm: "2px"
spacing:
  2xs: "4px"
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "40px"
  2xl: "64px"
components:
  button-publish:
    backgroundColor: "{colors.press-green}"
    textColor: "{colors.on-green}"
    rounded: "{rounded.sm}"
    padding: "12px 24px"
    height: "52px"
  button-publish-hover:
    backgroundColor: "{colors.press-green-deep}"
  button-publish-disabled:
    backgroundColor: "{colors.paper-sunk}"
    textColor: "{colors.ink-secondary}"
  button-press:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.sm}"
    height: "40px"
  button-press-hover:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
  input:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    height: "40px"
  drop-zone:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
---

# Design System: Supervision List

## Overview

The tool publishes its result the way a university publishes an admission or allocation list in a newspaper supplement: a masthead set only in type, a dense list ruled into equal columns, and a coordinator's blue biro marking what needs attention. It is an Operate surface for department coordinators who run it once or twice a year under time pressure, so every expressive choice also has to read in seconds.

Paper and ink carry everything. There are no cards, badges or shadows on content; hierarchy comes from type scale and weight alone, and structure comes from hairline and double rules. Two colours speak: press green means "publish" (one action per page), and biro blue means "a person should look at this or did something here".

The world is light by choice: an office under fluorescent light, a printed list pinned to a notice board.

## Colors

### Primary
- **Press Green** (`press-green`): the single primary action (Publish), the focused lecturer's top rule, the minimum-match readout. Never decoration.

### Secondary
- **Biro** (`biro`): every human or attention mark: weak matches circled, hand moves underlined, partial matches' row numerals, search hits (wavy underline), focus rings, caret, selection.

### Neutral
- **Newsprint** (`paper`): the page ground. `paper-raised` for drop zones and inputs; `paper-sunk` for disabled fills.
- **Ink** (`ink`), **Ink Secondary** (`ink-secondary`, all supporting text including italic field lines and row numerals), **Ink Muted** (`ink-muted`, borders of inputs and dashed drop zones only; never body text).
- **Rule** (`rule`) for heavy and double rules; **Rule Soft** (`rule-soft`) for hairlines between columns and rows.
- **Error** (`error`): file errors, over-limit loads, the "Not placed" column.

### Named Rules
**The Two Inks Rule.** Green is the press, blue is the pen. Green appears once per screen as an action; blue only ever marks a person's attention. Neither is used to decorate.

## Typography

Libre Franklin (newspaper gothic) for the masthead, headings, labels, counts and buttons; Spectral (screen serif) for names, prose and field text. Numbers are tabular lining figures everywhere.

### Hierarchy
- **Masthead**: Libre Franklin 900, fluid to 6rem, -0.035em, line-height 0.92. Only "Supervision List".
- **Section heads** ("The list", "How the list is set"): Libre Franklin 800–900, 1.6–2.25rem.
- **Lecturer names / slot headings**: Libre Franklin 800, 1.25rem.
- **Labels, counts, matric numbers**: Libre Franklin 600, 0.8125rem.
- **Names and prose**: Spectral 400, 1.0625rem / 1.55; field lines Spectral italic 0.8125rem in ink-secondary.

### Named Rules
**The Scale-Only Rule.** Hierarchy is made with size and weight. No eyebrows, kickers, uppercase tracked labels or coloured badges.

## Layout

A centred page up to 88rem with fluid side padding. The masthead sits over a double rule; the desk is a three-column grid (students, lecturers, rules) divided by hairlines, collapsing to two columns under 960px and one under 640px. The published list is an auto-fill grid of equal 17.5rem-minimum lecturer columns separated by hairline column rules, so every lecturer is set at the same scale. A fixed ink "press bar" holds counts and downloads once a list exists. Print hides the desk and press bar and prints the list alone.

## Elevation & Depth

Flat. The only shadows are a soft offset under the Publish button and a soft upward shadow on the press bar to lift it off the list. Content never floats.

## Shapes

Square paper. Radius is 0 for drop zones and 2px for buttons and inputs. Dashed hairline marks a place to drop a file. Rules are 1px hairline, 3px heavy, 3px double.

## Components

### Buttons
- **Publish**: press green fill, on-green Libre Franklin 800 at 1.25rem, 52px tall; hover deepens; disabled is paper-sunk with ink-secondary text.
- **Press bar buttons**: outline on ink, Libre Franklin 800; hover inverts to paper.
- **Text links**: underlined, 1px, 3px offset; hover turns biro.

### Inputs / Fields
Raised paper fill, ink-muted hairline border, 2px radius, 40px tall, Spectral text. Radio buttons and range sliders take press green via accent-color.

### Drop zone
Raised paper, dashed ink-muted border, centred two-line copy. Hover or drag-over: biro border and a faint biro wash. Busy: 60% opacity with progress cursor.

### Lecturer column (signature)
Heavy ink top rule; name in Libre Franklin 800; specialization in Spectral italic; a load bar of one cell per place (filled ink = taken, outline = free, error = over limit), drawn at the same cell width across all columns so lengths compare exactly; then a numbered name list with dotted row rules, matric numbers right-aligned. Clicking the head focuses the column: its rule turns green, other columns keep their text in ink-secondary and dim only bars and numerals.

### Biro marks (signature)
- Weak match: a hand-drawn-irregular biro oval around the name, rotated -2°.
- Partial match: the row numeral in bold biro.
- Moved by hand: name and matric in biro with a solid biro underline.
- Search hit: wavy biro underline.

### Move control
Clicking a name opens an inline native select under it, listing every lecturer ranked by match with their current load, plus "Leave unplaced". Escape closes it.

## Do's and Don'ts

### Do:
- Do keep one green action per screen.
- Do mark attention only in biro, with the pen's own vocabulary (circle, underline, numeral).
- Do keep every lecturer column at the same scale.
- Do let the list print cleanly on its own.

### Don't:
- Don't add cards, badges, pills, coloured side borders or icon tiles.
- Don't use ink-muted for text.
- Don't replay entrance motion on edits; the ink-in plays once, on publish.
- Don't introduce a dark theme by default; this world is printed paper.
