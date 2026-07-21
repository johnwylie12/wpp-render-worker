# meeting_label — "Let's start a conversation" QR meeting card

Standalone print asset for the ERA/WPP presentation folder. **Not queue-driven** —
fixed content (John's Book-With-Me QR + contact), so it is NOT wired into
`content_briefs` / `claim_next_brief` like the CIR. Run it only when the QR target
or the contact details change.

## Run
    python3 meeting_label.py out.pdf      # -> JohnWylie_MeetingLabel_6x4_sidebyside.pdf
Deps: pymupdf, qrcode, pillow.  Print at **100% / Actual Size** (no fit-to-page).

## LOCKED design (John, 2026-07-20/21)
- **6" W × 4" H, side-by-side** (vertical split at 3"). Chosen over the top/bottom
  fold layout because the label lies flat and a bigger, un-creased QR scans better.
- **LEFT (navy #003A70):** large QR (~2.14") + "Let's start a conversation" (white)
  + the **white VTI lockup** (white wordmark + gold underline + dot). ONE VTI only,
  and it lives here.
- **RIGHT (white):** ERA logo at **half size** + John Wylie · Senior Consultant,
  ERA Group · gold hairline · 703.244.9868 · jwylie@eragroup.com. **No VTI here.**
- QR: Book-With-Me `CMjo2-07uk2-Q0n_F1MSvQ2`, ERROR_CORRECT_M, verified decoding.

## Assets (assets/)
- `era_logo.png` — navy ERA wordmark (shared with case_study/closing).
- `vti_logo.png` — navy "value through insight™" wordmark (from note_card VTI_B64).
- `vti_white_lockup.png` — white wordmark + gold underline + dot, built from the
  real wordmark. ⚠️ **Upscaled from a 360×42 raster — soft up close.** Replace with
  the true high-res white VTI PNG from the brand folder when available (drop it in
  as `vti_white_lockup.png`, same aspect).

## Notes
- Title = Senior Consultant (2026-07-15 change). note_card/cover engines still say
  "Senior Advisor" — separate open item.
- `tbox()` auto-sizes text boxes to `max(h, fontsize*1.9)` to dodge PyMuPDF's
  silent text-drop when a box is a hair short.
