# Special thanks to the project maintainer Johnny A. Solbu for providing some of the
# settings here. https://www.solbu.net/

%global debug_package %{nil}
%define contentdir /var/www

Name:           hldig
Version:        1.0.2
Release:        1
Summary:        A web indexing and searching system for a small domain or intranet
Group:          Networking/WWW
License:        GPLv2
URL:            https://github.com/solbu/hldig/
Source0:        https://github.com/solbu/hldig/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        hldig.conf
Source2:        hldig-dbgen

Patch0:         hldig-rundiginfos.patch

BuildRequires:  libstdc++-devel
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(zlib)
BuildRequires:  db2-devel
BuildRequires:  gettext-devel
BuildRequires:  php-devel

Provides:       htdig >= 3.1.6

%description
The hl://Dig system is a complete world wide web indexing and searching
system for a small domain or intranet. This system is not meant to replace
the need for powerful internet-wide search systems like Google, DuckDuckGo,
Bing or Baidu. Instead it is meant to cover the search needs for a single
company, campus, or even a particular sub section of a web site. As
opposed to some WAIS-based or web-server based search engines, hl://Dig can
span several web servers at a site. The type of these different web servers
doesn't matter as long as they understand the HTTP 1.0 protocol.

hl://Dig was developed as "ht://Dig" at San Diego State University
as a way to search the various web servers on the campus network.

%package devel

Provides:       htdig-devel >= 3.1.6
Requires:       %{name} = %{version}

Summary:        Development package for %{name}

%description devel
Provides development libraries and debugging info for %{name}.

%package	web
Summary:        Scripts and HTML code needed for using hl://Dig as a web search engine
Group:          Networking/WWW
Requires:       %{name} = %{version}
Requires:       webserver

%description	web
The hl://Dig system is a complete world wide web indexing and searching
system for a small domain or intranet. This system is not meant to replace
the need for powerful internet-wide search systems like Google, DuckDuckGo,
Bing or Baidu. Instead it is meant to cover the search needs for a single
company, campus, or even a particular sub section of a web site. As
opposed to some WAIS-based or web-server based search engines, hl://Dig can
span several web servers at a site. The type of these different web servers
doesn't matter as long as they understand the HTTP 1.0 protocol.

hl://Dig was developed as "ht://Dig" at San Diego State University
as a way to search the various web servers on the campus network.

The %{name}-web package includes CGI scripts and HTML code needed to use
hl://Dig on a website.

%prep
%autosetup -p1
autoreconf --force --install

CXXFLAGS="%{?optflags} -std=c++14" \
LDFLAGS="" \
    ./configure --prefix=%{_prefix} \
        --sysconfdir=%{_sysconfdir} \
        --bindir=%{_bindir} \
        --libdir=%{_libdir} \
        --mandir=%{_mandir} \
        --localedir=%{_datadir}/locale \
        --datarootdir=%{_datadir} \
        --includedir=%{_includedir} \
        --localstatedir=%{_localstatedir} \
        --sharedstatedir=%{_sharedstatedir} \
        --enable-shared \
        --with-common-dir=%{contentdir}/html/%{name} \
        --with-database-dir=%{_sharedstatedir}/%{name} \
        --with-cgi-bin-dir=%{contentdir}/cgi-bin \
        --with-image-dir=%{contentdir}/html/%{name} \
        --with-image-url-prefix=/%{name} \
        --with-search-dir=%{contentdir}/html/%{name} \
        --with-apache=/usr/sbin/httpd \
        --with-default-config-file=%{_sysconfdir}/%{name}/%{name}.conf \

%build
%make_build

%install
%make_install

# install binary that was not included
install -m 755 %{_builddir}/%{name}-%{version}/hlsearch/hlsearch %{buildroot}/%{_bindir}

# add the service account
install -p -m 644 -D %{S:1} %{buildroot}%{_prefix}/lib/sysusers.d/%{name}.conf

# cron job
mkdir -p %{buildroot}/%{_sysconfdir}/cron.daily
cp %{S:2} %{buildroot}/%{_sysconfdir}/cron.daily/%{name}-dbgen

# set up /var/www
chmod 644 %{buildroot}%{contentdir}/html/%{name}/*
ln -sf ./search.html %{buildroot}%{contentdir}/html/%{name}/index.html

# migrate content to /usr/share and link it
mkdir -p %{buildroot}%{_datadir}
mv %{buildroot}%{contentdir}/html/hldig %{buildroot}%{_datadir}
ln -s %{_datadir}/%{name} %{buildroot}%{contentdir}/html/%{name}

%find_lang %{name}

%post web
# Only run this if installing for the first time
if [ "$1" = 1 ]; then
	if [ -f %{_sysconfdir}/httpd/conf/httpd.conf ];then
	SERVERNAME="`grep '^ServerName' %{_sysconfdir}/httpd/conf/httpd.conf | awk 'NR == 1 {print $2}'`"
	fi
	[ -z "$SERVERNAME" ] && SERVERNAME="`hostname -f`"
	[ -z "$SERVERNAME" ] && SERVERNAME="localhost"
	sed 's/^start_url:.*/#&\
# (See end of file for this parameter.)/' %{_sysconfdir}/hldig/hldig.conf > /tmp/hl.$$
	cat /tmp/hl.$$ > %{_sysconfdir}/%{name}/%{name}.conf
	rm /tmp/hl.$$
	cat >> %{_sysconfdir}/%{name}/%{name}.conf <<!

# Automatically set up by hldig RPM, from your current Apache httpd.conf...
# Verify and configure these, and set maintainer above, before running
# /usr/bin/rundig.
# See /usr/doc/hldig*/attrs.html for descriptions of attributes.

# The URL(s) where hldig will start.  See also limit_urls_to above.
start_url:	http://$SERVERNAME/

# This makes sure that we don't spider the web
local_urls_only: true

# These attributes allow indexing server via local filesystem rather than HTTP.
local_urls:	http://$SERVERNAME/=%{contentdir}/html/
local_user_urls:	http://$SERVERNAME/=/home/,/public_html/
!

fi

%files -f %{name}.lang
%license COPYING
%doc README.md ChangeLog
%{_bindir}/*
%{_datadir}/%{name}
%{_mandir}/man1/*.zst
%{_mandir}/man8/*.zst
%{_libdir}/%{name}/*.so
%{_libdir}/%{name}_db/*.so
%config(noreplace) %{_sysconfdir}/%{name}/cookies.txt
%config(noreplace) %{_sysconfdir}/%{name}/hldig.conf
%config(noreplace) %{_sysconfdir}/%{name}/HtFileType-magic.mime
%config(noreplace) %{_sysconfdir}/%{name}/mime.types

%files devel
%{_includedir}/%{name}
%{_includedir}/%{name}_db
%{_libdir}/%{name}/*.a
%{_libdir}/%{name}_db/*.a

%files web
%config(missingok, noreplace) %attr(0755,root,root) %{_sysconfdir}/cron.daily/%{name}-dbgen
%{contentdir}/html/%{name}
%{contentdir}/cgi-bin/*
%{_prefix}/lib/sysusers.d/%{name}.conf

