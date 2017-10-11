#._cv_part guppy.gsl.Html

class Node2Html:
    def __init__(self, mod, node=None, error_report = None, encode_name=None
                 ):
	self.mod = mod
        self.valid_html40 = False

	self.encode = self.mod.encode
	if encode_name is None:
	    encode_name = self.mod.encode_name
	self.encode_name = encode_name
	if error_report is not None:
	    self.error_report = error_report

        self.document_lang = None

        self.header_nodes = []


	self.indent = 0
	self.indentstep = 1

	self.set_out([])

        # xxx where do this?
        charset = 'utf-8'
        self.header_nodes.append(self.mod.node_of_taci(
            'meta', '', (
            self.mod.node_of_taci('http-equiv=', 'Content-Type'),
            self.mod.node_of_taci('content=',
                                  'text/html; charset=%s'%charset))))

	if node is not None:
	    node.accept(self)
	
    def _visit_children(self, node):
	node, attrs = node.split_attrs()
	# xxx handle attrs?
	E = self.mod.ReportedError
	for ch in node.children:
	    try:
		ch.accept(self)
	    except E:
		pass

    def begin(self, tag, arg=''):
	if arg:
	    t = '<%s %s>'%(tag, arg)
	else:
	    t = '<%s>'%tag
	if tag in self.mod.line_break_allowed:
	    t = '\n'+self.indent * ' ' + t
	self.append(t)
	self.indent += self.indentstep

    def chg_out(self, out):
	oo = self.out
	self.set_out(out)
	return oo

    def encode_link_name(self, name):
	# 1. Make the name better looking for a html user's perspective
	# 2. Encode it by HTML rules

	if name.startswith(self.mod.tgt_prefix):
	    name = name[len(self.mod.tgt_prefix):]
	else:
	    # Should not happen often or at all
	    assert 0
	name = self.encode_name(name)
	return name

    def end(self, tag):
	self.indent -= self.indentstep
	self.append('</%s>'%tag)

    def error(self, msg, *args, **kwds):
	msg = 'Doc2Html: ' + msg
	self.error_report(msg, *args, **kwds)

    def error_report(self, msg, *args, **kwds):
	print 'HTML ENCODING ERROR: ', msg, 'args=',args, 'kwds=',kwds
	raise ValueError

    def gen_document_header(self, lang, header_nodes):
	# lang & title are nodes with text or char directives, to be encoded.
	# metas is a list of nodes, with data to be encoded

	self.append("""\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN"
   "http://www.w3.org/TR/REC-html40/strict.dtd">
""")

	self.begin('html', 'lang=%s'%self.get_encoded_text(lang))
	self.begin('head')
        for node in header_nodes:
            self.gen_stdhtml(node)

	self.end('head')
        self.begin('body')

        # Get around w3c restriction that character data are not allowed
        # directly in body, makes it easier to write compliant code
        # Arguably the restriction is there for a reason, but I dont know...
        self.begin('div')

    def gen_document_trailer(self):
        self.end('div')
	self.end('body')
	self.end('html')

    def gen_empty_elmt(self, tag, arg=''):
	self.begin(tag, arg)
	self.indent -= self.indentstep

    def gen_generated_from_gsl(self):
	self.gen_empty_elmt('hr')

	self.append('Generated by ')
	self.begin('a', 'href="http://guppy-pe.sourceforge.net/gsl.html"')
	#self.begin('a', 'href="gsl.html"')
	self.append('GSL-HTML 0.1.5')
	self.end('a')
	self.append(' on '+self.mod.time.asctime(self.mod.time.localtime()))


    def gen_meta(self, node, tag=None):
	mknode = self.mod.node_of_taci
	if tag is None:
	    tag = node.tag
	self.header_nodes.append(
	    mknode('meta', '',
		   [mknode('name=', tag),
		    mknode('content=', node.arg, node.children)]))
	
    def gen_stdhtml(self, node, tag=None, **options):
	if tag is None:
	    tag = node.tag
	node, attrs = node.split_attrs(tag)
	self.begin(tag, ' '.join(['%s=%r'%(key, val) for (key, val) in attrs]))
        if tag in self.mod._no_end_tag_elements:
            if node.arg:
                self.error('No enclosed text allowed for Html tag: %r.'%node.tag)
            self.no_children(node)
            self.indent -= self.indentstep
        else:
            node.arg_accept(self)
            self.end(tag)


    def get_encoded_text(self, node):
	# From a node's arg and children that are text or characters
	old_out = self.chg_out([])
	self.append(self.encode(node.arg))
	for ch in node.children:
	    if ch.tag in ('text', 'char'):
		ch.accept(self)
	    else:
		self.error('Only text and char allowed here, not %r.'%ch.tag, ch)
	return ''.join(self.chg_out(old_out))

    def get_html(self):
	return ''.join(self.out)

    def no_children(self, node):
	if node.children:
	    self.error('No children allowed for %r. Got children nodes = %r.'%(
                node.tag, node.children))

    def set_out(self, out):
	self.out = out
	self.extend = out.extend
	self.append = out.append
	

    def visit_author(self, node):
	self.gen_meta(node)

    def visit_block(self, node):
	self._visit_children(node)

    def visit_char(self, node):
	name = node.get_namearg()
	if name in self.mod.name2codepoint:
	    name = '&%s;'%name
	else:
	    if name[:2] == "0x":
		char = int(name[2:], 16)
	    elif name.isdigit():
		char = int(name)
	    else:
		self.error('No such character: %r.'%name, node)
	    name = self.mod.codepoint2name.get(char)
	    if name is None:
		name = '&#%d;'%char
	    else:
		name = '&%s;'%name
	self.append(name)
	self._visit_children(node)
	

    def visit_col_width(self, node):
	self.append('<col width="%s" />'%node.arg)

    def visit_comment(self, node):
        return
        #self.append('<!-- %s -->'%node.arg)

    def visit_default(self, node):
	if node.tag in self.mod.stdhtml:
            if node.tag in self.mod._head_elements:
                self.head_nodes.append(node)
            else:
                self.gen_stdhtml(node)
	else:
	    self.error('I don\'t know what to generate for the tag %r.'%node.tag, node)

    def visit_define(self, node):
	name = self.encode_link_name(node.arg)
	self.begin('a', 'name=%r'%name)
	self._visit_children(node)
	self.end('a')

    def visit_document(self, node):
	self.indent = 2 # Known indentation of header to be generated later
	oldout = self.chg_out([])
	self._visit_children(node)

	self.gen_generated_from_gsl()

	newout = self.chg_out(oldout)
	mknode = self.mod.node_of_taci
	lang = self.document_lang
	if not lang:
	    lang = mknode('document_lang', 'en')

	self.indent = 0
	self.gen_document_header(lang, self.header_nodes)
	self.out.extend(newout)
	self.gen_document_trailer()

    def visit_document_lang(self, node):
	if self.document_lang is not None:
	    self.error('Duplicate document lang directive.', node)
	self.document_lang = node

    def visit_document_title(self, node):
        self.header_nodes.append(self.mod.node_of_taci('title', node.arg))

    def visit_enumerate(self, node):
	self.begin('ol')
	for c in node.children:
	    self.begin('li')
	    c.accept(self)
	    self.end('li')
	self.end('ol')

    def visit_exdefs(self, node):
	self.symplace = {}
	for ch in node.children:
	    syms = [x.strip() for x in ch.arg.split(',')]
	    for sym in syms:
		self.symplace[sym] = ch.tag

    def visit_header(self, node):
        self.header_nodes.extend(node.children)

    def visit_itemize(self, node):
	self.begin('ul')
	for c in node.children:
	    self.begin('li')
	    c.accept(self)
	    self.end('li')
	self.end('ul')

    def visit_link_to_extern(self, node):
	name = node.arg
	docname = node.children[0].arg
	children = node.children[1:]
	uri = '%s.html#%s'%(docname, self.encode_link_name(name))
	self.begin('a', 'href=%r'%uri)
	if not children:
	    self.append(self.encode(name))
	else:
	    for ch in children:
		ch.accept(self)
	self.end('a')
	

    def visit_link_to_local(self, node):
	name = node.arg
	uri = '#%s'%self.encode_link_name(name)
	self.begin('a', 'href=%r'%uri)
	if not node.children:
	    self.append(self.encode(name))
	else:
	    self._visit_children(node)
	self.end('a')

    def visit_link_to_unresolved(self, node):
	name = node.arg
	self.begin('em')
	if not node.children:
	    self.append(self.encode(name))
	else:
	    self._visit_children(node)
	self.end('em')

    def visit_literal_block(self, node):
	self.gen_stdhtml(node, 'pre')

    def visit_man_page_mode(self, node):
	self._visit_children(node)

    def visit_meta(self, node):
	self.document_metas.append(node)

    def visit_spc_colonkind(self, node):
	#self.append('&nbsp;<strong>:</strong>&nbsp;')
	#self.append('&nbsp;<code>:</code>&nbsp;')
	self.append('<code>:</code>&nbsp;')

    def visit_spc_mapsto(self, node):
	self.append(' <strong>-></strong> ')
	

    def visit_string(self, node):
	self._visit_children(node)

    def visit_symbol(self, node):
	self.visit_text(node)

    def visit_text(self, node):
	text = self.encode(node.arg)
	if len(text) > 80 or '\n' in text:
	    self.append('\n')
	self.append(text)
	self._visit_children(node)

    def visit_to_document_only(self, node):
	self._visit_children(node)

    def visit_to_html_only(self, node):
	self._visit_children(node)

    def visit_to_tester_only(self, node):
	pass

    def visit_valid_html40(self, node):
        self.valid_html40 = node

        node, attrs = self.valid_html40.split_attrs(attrdict=True)
        # XXX check allowed attrs but in a GENERAL way
        # Code taken from validator.w3.org
        self.append("""\
    <a href="http://validator.w3.org/check?uri=referer"><img
        src="%s"
        alt="Valid HTML 4.0 Strict" height="31" width="88"></a>
"""%attrs.get('src', 'http://www.w3.org/Icons/valid-html40'))


    def visit_with(self, node):
	pass

    def visit_word(self, node):
	self._visit_children(node)

class _GLUECLAMP_:
    _imports_ = (
	'_parent:SpecNodes',
	'_parent.SpecNodes:node_of_taci',
	'_parent.Gsml:is_not_ascii',
	'_parent.Main:tgt_prefix',
	'_parent.Main:ReportedError',
	'_root.htmlentitydefs:name2codepoint',
	'_root.htmlentitydefs:codepoint2name',
	'_root:re',
	'_root:time',
	)

    _chgable_ = ('tag_uppercase_name_chars',)

    # Set to make upper-case name characters tagged to make sure
    # no names in a file differ only in case as stated in HTML spec.
    # I believe this doesn't matter in practice in contemporary browsers,
    # since references are also said to be case sensitive!
    # -- I can't be bothered to solve this better now. See also Notes Aug 12 2005.
    tag_uppercase_name_chars = 0

    _html3_2 = (
	'a', 'address', 'area', 
	'b', 'base', 'big', 'blockquote', 'body', 'br',
	'caption', 'center', 'cite', 'code',
	'dfn', 'dt','dl', 'dd','div',
	'em', 'form',
	'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'html',
	'i', 'img', 'input', 'kbd',
	'li',
	'ol', 'option',
	'p', 'param', 'pre',
	'samp', 'select', 'small', 'strong', 'style', 'sub', 'sup',
	'table', 'td', 'textarea', 'th', 'thead', 'title', 'tr', 'tt', 
	'ul',
	'var')

    # Included in Html 3.2 but 'deprecated' in Html 4.0
    _html4_0_deprecated = (
	'applet', 'basefont', 'dir', 'font', 'isindex',
	'strike', 'u',
	)

    # Included in 3.2, not depreciated in 4.0 but one may want to avoid them
    _html_avoid = (
	'script',
    )
    _html4_0 = (
	'abbr', 'acronym',
	'bdo','button',
	'col', 'colgroup',
	'del',
	'fieldset', 'frame', 'frameset',
	'iframe', 'ins',
	'label', 'legend',
	'noframes', 'noscript',
	'object','optgroup',
	'q','s', 'span',
	'tbody', 'tfoot', 'thead')

    _head_elements = (
        'base','isindex','link','meta','script','style','title'
        )

    # The ones that can have no end tag
    # xxx are there more -style etc- look it up!
    _no_end_tag_elements = (
        # Header elmts
        'meta', 'link',
        # Other
        'img')

    # The ones that we may generate line-break before
    # and hope it will not affect the insertion of spaces in rendering.

    _line_break_allowed = (
	'html','head','body','frameset',
	# Head Elements
	) + _head_elements + (
	# Generic Block-level Elements
	'address','blockquote','center','del','div',
	'h1','h2','h3','h4','h5','h6','hr','ins','isindex','noscript','p','pre',
	# Lists
	'dir','dl','dt','dd','li','menu','ol','ul',
	# Tables
	'table','caption','colgroup','col','thead','tfoot','tbody','tr','td','th',
	# Forms
	'form','button','fieldset','legend','input','label',
	'select','optgroup','option','textarea'
	)


    # The attributes allowed in META elements
    meta_attributes = ('name', 'http-equiv', 'content', 'scheme', 'lang', 'dir')

    # This returns a function checking if a character is allowed to be used
    # as the first character in a NAME or ID attribute.
    #	(I don't think this is the same as .isalpha() with unicode.)

    def _get_is_name_starter_char(self):
	return self.re.compile(r"[A-Za-z]").match

    # This returns a function checking if a character is allowed to be used
    # after the first character in a NAME or ID attribute.

    def _get_is_name_follower_char(self):
	return self.re.compile(r"[A-Za-z0-9\-_:\.]").match


    # A set of the ones we generate directly.
    # This includes the ones from html 3.2 and
    # I have also included the deprecated and the 4.0 only


    def _get_stdhtml(self):
	sh = {}
	for x in self._html3_2 + self._html4_0_deprecated + self._html4_0:
	    sh[x] = 1
	return sh

    def _get_line_break_allowed(self):
	sh = {}
	for x in self._line_break_allowed:
	    sh[x] = 1
	return sh

    def doc2filer(self, doc, node, name, dir, opts, IO):
	text = self.doc2text(doc, node)
	path = IO.path.join(dir, '%s.html'%name)
	node = self.node_of_taci('write_file', path, [self.node_of_taci('text', text)])
	return node

    def doc2text(self, doc, node):
	d2h = Node2Html(self, node, doc.env.error)
	return d2h.get_html()

    def node2file(self, node, file):
	text = self.node2text(node)
	f = open(file, 'w')
	f.write(text)
	f.close()

    def node2text(self, node):
	text = Node2Html(self, node).get_html()
        return text

    # Adapted from html4css1.py in docutils

    def encode(self, text):
        """Encode special characters in `text` & return."""
        # @@@ A codec to do these and all other HTML entities would be nice.
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace('"', "&quot;")
        text = text.replace(">", "&gt;")
        text = text.replace("@", "&#64;") # may thwart some address harvesters
	return text
		    
    # Encode a name according to HTML spec. See also Notes Aug 12 2005.
    # From wdghtml40/values.html#cdata :
    # Attribute values of type ID and NAME must begin with a letter in the
    # range A-Z or a-z and may be followed by letters (A-Za-z), digits
    # (0-9), hyphens ("-"), underscores ("_"), colons (":"), and periods
    # ("."). These values are case-sensitive.

    def encode_name(self, name):
	is_name_follower_char = self.is_name_follower_char
	ns = []
	append = ns.append
	upperstate = 0

	ch = name[:1]
	if ch == 'z' or not self.is_name_starter_char(ch):
	    append('z')
	    if ch == 'z':
		append('z')
	for ch in name:
	    if ch == '-' or not is_name_follower_char(ch):
		if upperstate:
		    append('-')
		    upperstate = 0
		append('-')
		if ch != '-':
		    append('%d'%ord(ch))
		append('-')
	    elif ch.isupper() and self.tag_uppercase_name_chars:
		if not upperstate:
		    append('-')
		    upperstate = 1
		append(ch)
	    else:
		if upperstate:
		    append('-')
		    upperstate = 0
		append(ch)
	if upperstate:
	    append('-')
	return ''.join(ns)

