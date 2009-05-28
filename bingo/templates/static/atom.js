
function BingoLink(href, rel) {
    this.href = href;
    this.rel = rel;
}

BingoLink.prototype = {
    dumps: function() {
        var s = [];
        s.push('<link href="');
        s.push(this.href);
        s.push('"');
        if (this.rel != null) {
            s.push(' rel="');
            s.push(this.rel);
        }
        s.push('"/>');
        return s.join('');
    },
}

function BingoEntry(title, summary, links) {
    this.title = title;
    this.summary = summary;
    this.links = links;
}

BingoEntry.prototype = {
    dumps: function() {
        var s = [];
        s.push('<?xml version="1.0"?><entry xmlns="http://www.w3.org/2005/Atom"><title>');
        s.push(this.title);
        s.push('</title><summary>');
        s.push(this.summary);
        s.push('</summary>');
        for (i=0; i<this.links.length; i++) {
            s.push(this.links[i].dumps());
        }
        s.push('</entry>');
        return s.join('');
    },
}
