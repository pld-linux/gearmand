# TODO
# - fix make install linking stuff over again
# - skip tests build if testing disabled
# - logrotate
#
# Conditional build:
%bcond_with	tests		# build with tests
%bcond_without	gperftools	# gperftools
%bcond_without	sqlite3		# use SQLite 3 library
%bcond_without	tokyocabinet	# libtokyocabinet support
%bcond_without	memcached	# libmemcached support
%bcond_without	hiredis		# hiredis support
%bcond_without	pgsql		# PostgreSQL support via libpq
%bcond_without	mysql		# MySQL client library
%bcond_with	libdrizzle	# libdrizzle support

# google perftools available only on these
%ifnarch %{ix86} %{x8664} ppc64 ppc64le aarch64 %{arm}
%undefine	with_gperftools
%endif

Summary:	A distributed job system
Summary(pl.UTF-8):	System do rozpraszania zadań
Name:		gearmand
Version:	1.1.19.1
Release:	10
License:	BSD
Group:		Daemons
#Source0Download: https://github.com/gearman/gearmand/releases
Source0:	https://github.com/gearman/gearmand/archive/%{version}/%{name}-%{version}.tar.gz
# Source0-md5:	0c86283d6b82c390659d2bd7de6a9e1b
Source1:	%{name}.init
Source2:	%{name}.sysconfig
Source3:	%{name}.service
Patch0:		no-git.patch
Patch1:		x32.patch
URL:		http://www.gearman.org
BuildRequires:	autoconf >= 2.63
BuildRequires:	autoconf-archive
BuildRequires:	automake >= 1:1.11
BuildRequires:	boost-devel >= 1.39
BuildRequires:	gperf
%{?with_gperftools:BuildRequires:	gperftools-devel}
%{?with_hiredis:BuildRequires:	hiredis-devel}
BuildRequires:	libevent-devel
%{?with_memcached:BuildRequires:	libmemcached-devel}
BuildRequires:	libstdc++-devel >= 6:4.3
BuildRequires:	libtool >= 2:2.2
BuildRequires:	libuuid-devel
%{?with_mysql:BuildRequires:	mysql-devel}
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig
%{?with_pgsql:BuildRequires:	postgresql-devel}
BuildRequires:	rpmbuild(macros) >= 1.647
BuildRequires:	sphinx-pdg >= 1.0
%{?with_sqlite3:BuildRequires:	sqlite3-devel}
%{?with_tokyocabinet:BuildRequires:	tokyocabinet-devel}
BuildRequires:	zlib-devel
%if %{with tests}
BuildRequires:	curl-devel >= 7.21.7
BuildRequires:	mysql-server
%endif
Provides:	group(gearmand)
Provides:	user(gearmand)
Requires(post,preun):	/sbin/chkconfig
Requires(post,preun,postun):	systemd-units >= 38
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	libgearman = %{version}-%{release}
Requires:	procps
Requires:	rc-scripts >= 0.4.0.17
Requires:	systemd-units >= 0.38
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Gearman provides a generic framework to farm out work to other
machines or dispatch function calls to machines that are better suited
to do the work. It allows you to do work in parallel, to load balance
processing, and to call functions between languages. It can be used in
a variety of applications, from high-availability web sites to the
transport for database replication. In other words, it is the nervous
system for how distributed processing communicates.

%description -l pl.UTF-8
Gearman zapewnia ogólny szkielet do rozpraszania zadań na inne maszyny
lub ekspediowania wywołań funkcji na maszyny lepiej przystosowane do
danego zadania. Pozwala wykonywać zadania równolegle, równoważyć
obciążenie oraz wykonywać wywołania funkcji między językami. Może być
używany w wielu zastosowaniach, od wysoko dostępnych storn WWW do
transportu na potrzeby replikacji bazy danych. Innymi słowy, jest to
układ nerwowy, zapewniający komunikację przy przetwarzaniu
rozproszonym.

%package -n libgearman
Summary:	Shared gearman library
Summary(pl.UTF-8):	Biblioteka współdzielona gearman
Group:		Libraries
Provides:	libgearman-1.0 = %{version}-%{release}
Obsoletes:	libgearman-1.0 < %{version}-%{release}
# gearman requires uuid_generate_time_safe, which only exists in newer e2fsprogs-libs
Requires:	e2fsprogs-libs >= 1.39-32

%description -n libgearman
Shared gearman library.

%description -n libgearman -l pl.UTF-8
Biblioteka współdzielona gearman.

%package -n libgearman-devel
Summary:	Development headers for libgearman
Summary(pl.UTF-8):	Pliki nagłówkowe biblioteki libgearman
Group:		Development/Libraries
Requires:	libevent-devel
Requires:	libgearman = %{version}-%{release}
Provides:	libgearman-1.0-devel = %{version}-%{release}
Obsoletes:	libgearman-1.0-devel < %{version}-%{release}

%description -n libgearman-devel
Development headers for libgearman.

%description -n libgearman-devel -l pl.UTF-8
Pliki nagłówkowe biblioteki libgearman.

%prep
%setup -q
%patch0 -p1
%ifarch x32
%patch1 -p1
%endif

echo "m4_define([VERSION_NUMBER], %{version})" > version.m4

%build
%{__libtoolize}
%{__aclocal}
%{__autoconf}
%{__autoheader}
%{__automake}
%configure \
	--disable-silent-rules \
	--disable-static \
	%{__enable_disable hiredis} \
	%{__enable_disable libdrizzle} \
	%{__enable_disable memcached libmemcached} \
	%{__enable_disable pgsql libpq} \
	%{__enable_disable tokyocabinet libtokyocabinet} \
	%{__with_without mysql} \
	%{__with_without sqlite3} \
	--disable-wolfssl \
	--enable-ssl \
	--disable-dtrace

%{__make} -C docs  -j1
%{__make} -j1

%if %{with tests}
%{__make} check
%endif

%install
rm -rf $RPM_BUILD_ROOT

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

%{__rm} $RPM_BUILD_ROOT%{_libdir}/libgearman*.la

install -d $RPM_BUILD_ROOT/etc/{rc.d/init.d,sysconfig} \
	$RPM_BUILD_ROOT{%{_sysconfdir}/%{name},%{systemdunitdir},%{systemdtmpfilesdir}} \
	$RPM_BUILD_ROOT/var/{log,run/gearmand}

cp -p %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/gearmand
cp -p %{SOURCE3} $RPM_BUILD_ROOT%{systemdunitdir}/%{name}.service
install -p %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/gearmand
touch $RPM_BUILD_ROOT/var/log/gearmand.log

cat >$RPM_BUILD_ROOT%{systemdtmpfilesdir}/gearmand.conf <<EOF
d /var/run/gearmand 0771 root gearmand -
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 328 gearmand
%useradd -u 328 -g gearmand -d / -s /sbin/nologin -c "Gearmand job server" gearmand

%post
test -e /var/log/gearmand.log || touch /var/log/gearmand.log
/sbin/chkconfig --add gearmand
%service gearmand restart
%systemd_post gearmand.service

%preun
if [ "$1" = 0 ] ; then
	%service gearmand stop
	/sbin/chkconfig --del gearmand
fi
%systemd_preun gearmand.service

%postun
%systemd_reload
if [ "$1" = "0" ]; then
	%userremove gearmand
	%groupremove gearmand
fi

%post	-n libgearman -p /sbin/ldconfig
%postun	-n libgearman -p /sbin/ldconfig

%files
%defattr(644,root,root,755)
%doc README.md
%attr(754,root,root) /etc/rc.d/init.d/gearmand
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/gearmand
%attr(755,root,root) %{_sbindir}/gearmand
%attr(755,root,root) %{_bindir}/gearman
%attr(755,root,root) %{_bindir}/gearadmin
%{_mandir}/man1/gearadmin.1*
%{_mandir}/man1/gearman.1*
%{_mandir}/man8/gearmand.8*
%{systemdunitdir}/%{name}.service
%{systemdtmpfilesdir}/gearmand.conf
%dir %attr(771,root,gearmand) /var/run/gearmand
%attr(640,gearmand,gearmand) %config(noreplace) %verify(not md5 mtime size) /var/log/gearmand.log

%files -n libgearman
%defattr(644,root,root,755)
%doc AUTHORS COPYING ChangeLog
%attr(755,root,root) %{_libdir}/libgearman.so.*.*.*
%attr(755,root,root) %ghost %{_libdir}/libgearman.so.8

%files -n libgearman-devel
%defattr(644,root,root,755)
%attr(755,root,root) %{_libdir}/libgearman.so
%{_includedir}/libgearman
%{_includedir}/libgearman-1.0
%{_pkgconfigdir}/gearmand.pc
%{_mandir}/man3/gearman_*.3*
%{_mandir}/man3/libgearman.3*
