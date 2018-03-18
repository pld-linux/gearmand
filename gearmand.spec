# TODO
# - fix make install linking stuff over again
# - skip tests build if testing disabled
# - libpq vs postgresql, which one matters?
# - tmpfiles conf
# - logrotate
#
# Conditional build:
%bcond_with	tests		# build with tests
%bcond_without	gperftools	# gperftools
%bcond_without	sqlite3		# use SQLite 3 library [default=yes]
%bcond_without	libtokyocabinet	# Build with libtokyocabinet support [default=on]
%bcond_without	libmemcached	# Build with libmemcached support [default=on]
%bcond_without	hiredis	# Build with hiredis support [default=on]
%bcond_without	libpq	# Build with libpq, ie Postgres, support [default=on]
%bcond_without	mysql	# use MySQL client library [default=yes]
%bcond_without	postgresql	# use PostgreSQL library [default=yes]
%bcond_with	libdrizzle	# Build with libdrizzle support [default=on]

# google perftools available only on these
%ifnarch %{ix86} x86_64 ppc64 ppc64le aarch64 %{arm}
%undefine	with_gperftools
%endif

Summary:	A distributed job system
Name:		gearmand
Version:	1.1.18
Release:	1
License:	BSD
Group:		Daemons
Source0:	https://github.com/gearman/gearmand/archive/%{version}/%{name}-%{version}.tar.gz
# Source0-md5:	e947647db2a23239cead1c0960f2b5a0
Source1:	%{name}.init
Source2:	%{name}.sysconfig
Source3:	%{name}.service
Patch0:		no-git.patch
URL:		http://www.gearman.org
BuildRequires:	autoconf
BuildRequires:	autoconf-archive
BuildRequires:	automake
BuildRequires:	boost-devel >= 1.37.0
BuildRequires:	gperf
%{?with_gperftools:BuildRequires:	gperftools-devel}
%{?with_hiredis:BuildRequires:	hiredis-devel}
BuildRequires:	libevent-devel
%{?with_libmemcached:BuildRequires:	libmemcached-devel}
BuildRequires:	libtool
BuildRequires:	libuuid-devel
%{?with_mysql:BuildRequires:	mysql-devel}
BuildRequires:	pkgconfig
BuildRequires:	postgresql-devel
%{?with_libpq:BuildRequires:	postgresql-devel}
BuildRequires:	rpmbuild(macros) >= 1.647
%{?with_sqlite3:BuildRequires:	sqlite3-devel}
%{?with_tokyocabinet:BuildRequires:	tokyocabinet-devel}
BuildRequires:	zlib-devel
%if %{with tests}
BuildRequires:	curl-devel
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
Requires:	procps
Requires:	rc-scripts >= 0.4.0.17
Requires:	systemd-units >= 0.38
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

# FIXME: add tmpfiles conf
%define		no_install_post_check_tmpfiles	1

%description
Gearman provides a generic framework to farm out work to other
machines or dispatch function calls to machines that are better suited
to do the work. It allows you to do work in parallel, to load balance
processing, and to call functions between languages. It can be used in
a variety of applications, from high-availability web sites to the
transport for database replication. In other words, it is the nervous
system for how distributed processing communicates.

%package -n libgearman
Summary:	Development libraries for gearman
Group:		Development/Libraries
Provides:	libgearman-1.0 = %{version}-%{release}
Obsoletes:	libgearman-1.0 < %{version}-%{release}
# gearman requires uuid_generate_time_safe, which only exists in newer e2fsprogs-libs
Requires:	e2fsprogs-libs >= 1.39-32

%description -n libgearman
Development libraries for %{name}.

%package -n libgearman-devel
Summary:	Development headers for libgearman
Group:		Development/Libraries
Requires:	libevent-devel
Requires:	libgearman = %{version}-%{release}
Provides:	libgearman-1.0-devel = %{version}-%{release}
Obsoletes:	libgearman-1.0-devel < %{version}-%{release}

%description -n libgearman-devel
Development headers for %{name}.

%prep
%setup -q
%patch0 -p1

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
	%{__enable_disable libmemcached} \
	%{__enable_disable libpq} \
	%{__enable_disable libtokyocabinet} \
	%{__with_without mysql} \
	%{__with_without postgresql} \
	%{__with_without sqlite3} \
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

rm -v $RPM_BUILD_ROOT%{_libdir}/libgearman*.la

install -d $RPM_BUILD_ROOT/etc/{rc.d/init.d,sysconfig} \
	$RPM_BUILD_ROOT{%{_sysconfdir}/%{name},%{systemdunitdir}} \
	$RPM_BUILD_ROOT/var/{run/gearmand,log}

cp -p %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/gearmand
cp -p %{SOURCE3} $RPM_BUILD_ROOT%{systemdunitdir}/%{name}.service
install -p %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/gearmand
touch $RPM_BUILD_ROOT/var/log/gearmand.log

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
%dir %attr(771,root,gearmand) /var/run/gearmand
%attr(640,gearmand,gearmand) %config(noreplace) %verify(not md5 mtime size) /var/log/gearmand.log

%files -n libgearman
%defattr(644,root,root,755)
%doc COPYING
%attr(755,root,root) %{_libdir}/libgearman.so.*.*.*
%ghost %{_libdir}/libgearman.so.8

%files -n libgearman-devel
%defattr(644,root,root,755)
%doc AUTHORS ChangeLog
%{_includedir}/libgearman
%{_pkgconfigdir}/gearmand.pc
%{_libdir}/libgearman.so
%{_includedir}/libgearman-1.0
%{_mandir}/man3/gearman_*
%{_mandir}/man3/libgearman.3*
