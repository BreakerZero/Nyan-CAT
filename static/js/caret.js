function getCaretTopPoint () {
      const sel = document.getSelection()
      const r = sel.getRangeAt(0)
      let rect
      let r2
      const node = r.startContainer
      const offset = r.startOffset
      const posbody = document.body.getBoundingClientRect()
      if (offset > 0) {
        // new range, don't influence DOM state
        r2 = document.createRange()
        r2.setStart(node, (offset - 1))
        r2.setEnd(node, offset)
        rect = r2.getBoundingClientRect()
        return { left: rect.right, top: (rect.top-posbody.top) }
      } else if (offset < node.length) {
        r2 = document.createRange()
        // similar but select next on letter
        r2.setStart(node, offset)
        r2.setEnd(node, (offset + 1))
        rect = r2.getBoundingClientRect()
        return { left: rect.left, top: (rect.top-posbody.top) }
      } else {
        rect = node.getBoundingClientRect()
        const styles = getComputedStyle(node)
        const lineHeight = parseInt(styles.lineHeight)
        const fontSize = parseInt(styles.fontSize)
        // roughly half the whitespace... but not exactly
        const delta = (lineHeight - fontSize) / 2
        return { left: rect.left, top: (rect.top - posbody.top  + delta) }
}}