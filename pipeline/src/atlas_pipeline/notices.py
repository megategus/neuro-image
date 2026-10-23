"""Third-party licence notices shipped with the site data (NOTICES.txt)."""
from __future__ import annotations

REPO_URL = "https://github.com/megategus/neuro-image"
GPL_URL = "https://www.gnu.org/licenses/gpl-3.0.html"

# Verbatim from TemplateFlow's copy of the MNI ICBM152 2009 licence
# (https://templateflow.s3.amazonaws.com/tpl-MNI152NLin2009cSym/LICENSE).
# Redistribution requires that this notice appear in all copies.
MNI_NOTICE = """Copyright (C) 1993-2004 Louis Collins, McConnell Brain
Imaging Centre, Montreal Neurological Institute, McGill University.
Permission to use, copy, modify, and distribute this software and
its documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies.  The
authors and McGill University make no representations about the
suitability of this software for any purpose.  It is provided "as
is" without express or implied warranty.  The authors are not
responsible for any data loss, equipment damage, property loss, or
injury to subjects or patients resulting from the use or misuse of
this software package."""

# Verbatim from https://raw.githubusercontent.com/ThomasYeoLab/CBIG/master/LICENSE.md
CBIG_MIT_NOTICE = """Copyright (c) 2016 Computational Brain Imaging Group (CBIG)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""


def notices_text(maps: list[dict], atlas_sources: list[dict], template: dict) -> str:
    """Plain-text notices for every third-party file the site ships or derives from."""
    out = [
        "Brain Condition Atlas: third-party notices",
        "",
        f"Source code (Corresponding Source): {REPO_URL}",
        f"The site and its data files are distributed under GPL-3.0: {GPL_URL}",
        "Each third-party file below keeps its own licence.",
        "",
        "== Maps (maps/*.nii.gz) ==",
    ]
    groups: dict[tuple[str, str, str], list[str]] = {}
    for m in maps:
        groups.setdefault((m["citation"], m["doi"], m["licence"]), []).append(m["label"])
    for (citation, doi, licence), labels in groups.items():
        out += [f"{', '.join(labels)}:", f"  {citation} doi:{doi}", f"  Licence: {licence}", ""]
    out += [
        "== Background template (template.nii.gz) ==",
        template["name"],
        f"Licence: {template['licence']}",
        "",
        template.get("notice", ""),
        "",
        "== Reference atlases ==",
    ]
    for s in atlas_sources:
        shipped = ("shipped as atlas_labels.nii.gz (derived, labels only)" if s.get("bundled")
                   else "used to compute network profiles only; not distributed")
        out += [s["name"], f"  {s['citation']}", f"  Licence: {s['licence']}", f"  {shipped}"]
        if s.get("notice"):
            out += ["", s["notice"]]
        out.append("")
    return "\n".join(out).rstrip() + "\n"
