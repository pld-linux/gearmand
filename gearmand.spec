# TODO
# - fix make install linking stuff over again
# - skip tests build if testing disabled
# - add gearman user/group
#
# Conditional build:
%bcond_with	tests		# build with tests
%bcond_without	gperftools	# gperftools
%bcond_without	sqlite		# sqlite
%bcond_without	tokyocabinet	# tokyocabinet
%bcond_with	tcmalloc	# tcmalloc

# google perftools available only on these
%ifnarch %{ix86} x86_64 ppc64 ppc64le aarch64 %{arm}
%undefine	with_gperftools
%endif

%ifarch ppc64 sparc64
%undefine	with_tcmalloc
%endif

Summary:	A distributed job system
Name:		gearmand
Version:	1.1.12
Release:	0.1
License:	BSD
Group:		Daemons
Source0:	https://launchpad.net/gearmand/1.2/%{version}/+download/%{name}-%{version}.tar.gz
# Source0-md5:	99dd0be85b181eccf7fb1ca3c2a28a9f
Source1:	%{name}.init
Source2:	%{name}.sysconfig
Source3:	%{name}.service
Patch0:		%{name}-1.1.12-ppc64le.patch
URL:		http://www.gearman.org
BuildRequires:	boost-devel >= 1.37.0
BuildRequires:	gperf
%{?with_gperftools:BuildRequires:	gperftools-devel}
BuildRequires:	libevent-devel
BuildRequires:	libmemcached-devel
BuildRequires:	libuuid-devel
#BuildRequires:	memcached
BuildRequires:	mysql-devel
BuildRequires:	pkgconfig
BuildRequires:	postgresql-devel
BuildRequires:	rpmbuild(macros) >= 1.647
%{?with_sqlite:BuildRequires:	sqlite3-devel}
%{?with_tokyocabinet:BuildRequires:	tokyocabinet-devel}
BuildRequires:	zlib-devel
%if %{with tests}
BuildRequires:	curl-devel
BuildRequires:	mysql-server
%endif
Requires(post,preun):	/sbin/chkconfig
Requires(post,preun,postun):	systemd-units >= 38
Requires:	procps
Requires:	rc-scripts
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

%build
# HACK to work around boost issues.
#export LDFLAGS="%{rpmldflags} LDFLAGS -lboost_system"

%configure \
	--disable-silent-rules \
	--disable-static \
%if %{with tcmalloc}
	--enable-tcmalloc \
%endif

%{__make}

%if %{with tests}
%{__make} check
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

rm -v $RPM_BUILD_ROOT%{_libdir}/libgearman*.la

install -p -D %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/gearmand

# install systemd unit file
install -d $RPM_BUILD_ROOT%{systemdunitdir}
cp -p %{SOURCE3} $RPM_BUILD_ROOT%{systemdunitdir}/%{name}.service

# install legacy SysV init script
install -p -D %{SOURCE1} $RPM_BUILD_ROOT%{_initrddir}/gearmand
install -d $RPM_BUILD_ROOT/var/run/gearmand

install -d $RPM_BUILD_ROOT/var/log
touch $RPM_BUILD_ROOT/var/log/gearmand.log

install -d $RPM_BUILD_ROOT/var/run/gearmand

%clean
rm -rf $RPM_BUILD_ROOT

%if 0
%pre
%groupadd -r gearmand
%useradd -r -g gearmand -d / -s /sbin/nologin -c "Gearmand job server" gearmand

%post
%systemd_post gearmand.service
if [ $1 = 1 ]; then
	/sbin/chkconfig --add gearmand
fi
touch /var/log/gearmand.log

%preun
%systemd_preun gearmand.service
if [ "$1" = 0 ] ; then
	%service gearmand stop
	/sbin/chkconfig --del gearmand
fi

%postun
%systemd_postun_with_restart gearmand.service
%endif

%post	-n libgearman -p /sbin/ldconfig
%postun	-n libgearman -p /sbin/ldconfig

%files
%defattr(644,root,root,755)
%doc README
%attr(755,gearmand,gearmand) /var/run/gearmand
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/gearmand
%attr(755,root,root) %{_sbindir}/gearmand
%attr(755,root,root) %{_bindir}/gearman
%attr(755,root,root) %{_bindir}/gearadmin
%{_mandir}/man1/*
%{_mandir}/man8/*
%attr(640,gearmand,gearmand) %config(noreplace) %verify(not md5 mtime size) /var/log/gearmand.log
%if %{with systemd}
%{systemdunitdir}/%{name}.service
%else
%{_initrddir}/%{name}
%endif

%files -n libgearman
%defattr(644,root,root,755)
%doc COPYING
%attr(755,root,root) %{_libdir}/libgearman.so.*.*.*
%ghost %{_libdir}/libgearman.so.8

%files -n libgearman-devel
%defattr(644,root,root,755)
%doc AUTHORS ChangeLog
%dir %{_includedir}/libgearman
%{_includedir}/libgearman/*.h
%{_pkgconfigdir}/gearmand.pc
%{_libdir}/libgearman.so
%{_includedir}/libgearman-1.0
%{_mandir}/man3/*
