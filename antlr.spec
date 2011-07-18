# Copyright (c) 2000-2005, JPackage Project
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the JPackage Project nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

%define with_mono %{?_with_mono:1}%{!?_with_mono:%{?rhel:0}%{!?rhel:1}}

%define build_jedit  %{?_with_jedit:1}%{!?_with_jedit:0}

%define section free
%define native  %{?_with_native:1}%{!?_with_native:0}

%global debug_package %{nil}

Summary:        ANother Tool for Language Recognition
Name:           antlr
Version:        2.7.7
Release:        6.5%{?dist}
Epoch:          0
License:        Public Domain
URL:            http://www.antlr.org/
Group:          Development/Code Generators
Source0:        http://www.antlr2.org/download/antlr-%{version}.tar.gz
Source1:        %{name}-build.xml
Source2:        %{name}-script
#http://www.antlr.org/share/1069557132934/makefile.gcj
Source3:        makefile.gcj
Patch0:         %{name}-jedit.patch
Patch1:         %{name}-%{version}-newgcc.patch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-buildroot

%if %{native}
BuildRequires:  %{_bindir}/gcj, %{__make}
%else
BuildRequires:  ant

%if 0%{?with_mono}
%ifnarch s390 s390x ppc64 sparc64
BuildRequires:  mono-core
BuildRequires:  mono-winforms
%endif
%endif

BuildRequires:  %{__perl}, java-javadoc
Requires:       jpackage-utils
Requires(post): %{_sbindir}/update-alternatives
Requires(postun): %{_sbindir}/update-alternatives
%endif

%description
ANTLR, ANother Tool for Language Recognition, (formerly PCCTS) is a
language tool that provides a framework for constructing recognizers,
compilers, and translators from grammatical descriptions containing
C++ or Java actions [You can use PCCTS 1.xx to generate C-based
parsers].

%package        native
Group:          Development/Code Generators
Summary:        ANother Tool for Language Recognition (native version)
Requires(post): %{_sbindir}/update-alternatives
Requires(postun): %{_sbindir}/update-alternatives

%description    native
ANTLR, ANother Tool for Language Recognition, (formerly PCCTS) is a
language tool that provides a framework for constructing recognizers,
compilers, and translators from grammatical descriptions containing
C++ or Java actions [You can use PCCTS 1.xx to generate C-based
parsers].  This package includes the native version of the antlr tool.

%package        manual
Group:          Development/Code Generators
Summary:        Manual for %{name}

%description    manual
Documentation for %{name}.

%package        javadoc
Group:          Development/Documentation
Summary:        Javadoc for %{name}

%description    javadoc
Javadoc for %{name}.

%if %{build_jedit}
%package        jedit
Group:          Text Editors
Summary:        ANTLR mode for jEdit
Requires:       jedit >= 0:4.1

%description    jedit
ANTLR mode for jEdit.  To enable this mode, insert the following into your
%{_datadir}/jedit/modes/catalog:

  <MODE NAME="antlr" FILE="antlr.xml" FILE_NAME_GLOB="*.g"/>
%endif

%prep
%setup -q
# remove all binary libs
find . -name "*.jar" -exec rm -f {} \;
%if !%{native}
%patch0 -p0
cp -p %{SOURCE1} build.xml
# fixup paths to manual
%{__perl} -pi -e 's|"doc/|"%{_docdir}/%{name}-manual-%{version}/|g' \
  install.html
%endif

%patch1

%build
%if %{native}
%{__make} -f %{SOURCE3} COMPOPTS="$RPM_OPT_FLAGS"

%else
ant -Dj2se.apidoc=%{_javadocdir}/java
cp work/lib/antlr.jar .  # make expects to find it here
export CLASSPATH=.
%configure --without-examples
make CXXFLAGS="${CXXFLAGS} -fPIC"

find . -type f > /tmp/antlr.filelist
rm antlr.jar             # no longer needed
%endif


%install
rm -rf $RPM_BUILD_ROOT

install -dm 755 $RPM_BUILD_ROOT%{_bindir}
touch $RPM_BUILD_ROOT%{_bindir}/antlr # for %%ghost

%if %{native}

install -pm 755 cantlr $RPM_BUILD_ROOT%{_bindir}/antlr-native

%else
# jars
mkdir -p $RPM_BUILD_ROOT%{_javadir}
cp -p work/lib/%{name}.jar $RPM_BUILD_ROOT%{_javadir}/%{name}-%{version}.jar
(cd $RPM_BUILD_ROOT%{_javadir} && for jar in *-%{version}.jar; do ln -sf ${jar} `echo $jar| sed "s|-%{version}||g"`; done)

# script
cp -p %{SOURCE2} $RPM_BUILD_ROOT%{_bindir}/antlr-java

# C++ lib and headers, antlr-config
%define headers %{_includedir}/%{name}

mkdir -p $RPM_BUILD_ROOT{%{headers},%{_libdir}}
install -m 644 lib/cpp/antlr/*.hpp $RPM_BUILD_ROOT%{headers}
install -m 644 lib/cpp/src/libantlr.a $RPM_BUILD_ROOT%{_libdir}
install -m 755 scripts/antlr-config $RPM_BUILD_ROOT%{_bindir}

# javadoc
mkdir -p $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
cp -pr work/api/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
ln -s %{name}-%{version} $RPM_BUILD_ROOT%{_javadocdir}/%{name}

# jedit mode
%if %{build_jedit}
mkdir -p $RPM_BUILD_ROOT%{_datadir}/jedit/modes
cp -p extras/antlr-jedit.xml $RPM_BUILD_ROOT%{_datadir}/jedit/modes/antlr.xml
%endif
%endif

%clean
rm -rf $RPM_BUILD_ROOT


%post
%{_sbindir}/update-alternatives --install %{_bindir}/antlr \
  %{name} %{_bindir}/antlr-java 10

%postun
if [ $1 -eq 0 ] ; then
  %{_sbindir}/update-alternatives --remove %{name} %{_bindir}/antlr-java
fi

%if %{native}

%post native
%{_sbindir}/update-alternatives --install %{_bindir}/antlr \
  %{name} %{_bindir}/antlr-native 20

%postun native
if [ $1 -eq 0 ] ; then
  %{_sbindir}/update-alternatives --remove %{name} %{_bindir}/antlr-native
fi
%endif

%if %{native}
%files native
%defattr(0644,root,root,0755)
%doc INSTALL.txt LICENSE.txt
%defattr(0755,root,root,0755)
%ghost %{_bindir}/antlr
%{_bindir}/antlr-native

%else
%files
%defattr(0644,root,root,0755)
%doc INSTALL.txt LICENSE.txt
%{_javadir}/%{name}*.jar
%{headers}
%{_libdir}/libantlr.a
%defattr(0755,root,root,0755)
%ghost %{_bindir}/antlr
%{_bindir}/antlr-config
%{_bindir}/antlr-java

%files manual
%defattr(0644,root,root,0755)
%doc doc/*

%files javadoc
%defattr(0644,root,root,0755)
%doc %{_javadocdir}/%{name}-%{version}
%doc %{_javadocdir}/%{name}

%if %{build_jedit}
%files jedit
%defattr(0644,root,root,0755)
%{_datadir}/jedit/modes/*
%endif
%endif


%changelog
* Tue Jun 8 2010 Alexander Kurtakov <akurtako@redhat.com> 0:2.7.7-6.5
- Disable empty debuginfo.

* Mon Jun 7 2010 Alexander Kurtakov <akurtako@redhat.com> 0:2.7.7-6.4
- This is not a noarch package, it contains native libraries.

* Sun Jan 10 2010 Alexander Kurtakov <akurtako@redhat.com> 0:2.7.7-6.3
- Use upstream sources.

* Thu Dec 03 2009 Dennis Gregorovic <dgregor@redhat.com> - 0:2.7.7-6.2
- Rebuilt for RHEL 6

* Fri Nov 13 2009 Dennis Gregorovic <dgregor@redhat.com> - 0:2.7.7-6.1
- disable mono on RHEL

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0:2.7.7-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Fri Mar 20 2009 Deepak Bhole <dbhole@redhat.com> - 0:2.7.7-5
- Include cstdio in CharScanner.hpp (needed to build with GCC 4.4)
- Merge changes from includestrings patch into the above one

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0:2.7.7-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Fri Jan 09 2009 Dennis Gilmore <dennis@ausil.us> 2.7.7-3
- exlcude using mono on sparc64

* Wed Jul  9 2008 Tom "spot" Callaway <tcallawa@redhat.com> 2.7.7-2
- drop repotag

* Wed Feb 27 2008 Deepak Bhole <dbhole@redhat.com> - 0:2.7.7-1jpp.7
- Add strings inclusion (for GCC 4.3)

* Mon Sep 24 2007 Deepak Bhole <dbhole@redhat.com> - 0:2.7.7-1jpp.6
- Resolve bz# 242305: Remove libantlr-pic.a, and compile libantlr.a with fPIC

* Wed Aug 29 2007 Fedora Release Engineering <rel-eng at fedoraproject dot org> - 2.7.7-1jpp.5
- Rebuild for selinux ppc32 issue.

* Tue Jun 12 2007 Deepak Bhole <dbhole@redhat.com> 2.7.7-1jpp.4.fc8
- Added a PIC compiled archive (bz# 242305)

* Thu Jun 07 2007 Deepak Bhole <dbhole@redhat.com> 2.7.7-1jpp.3
- Applied patch to fix conditionals (from skasal at redhat dot com)

* Mon Mar 26 2007 Deepak Bhole <dbhole@redhat.com> 2.7.7-1jpp.2
- Added unowned dir to files list

* Fri Jan 19 2007 Deepak Bhole <dbhole@redhat.com> 0:2.7.7-1jpp.1
- Upgrade to 2.7.7
- Resolve 172456 with patches from Vadim Nasardinov and Radu Greab

* Thu Aug 03 2006 Deepak Bhole <dbhole@redhat.com> = 0:2.7.6-4jpp.2
- Add missing postun for javadoc.

* Thu Aug 03 2006 Deepak Bhole <dbhole@redhat.com> = 0:2.7.6-4jpp.1
- Add missing requirements.

* Sat Jul 22 2006 Thomas Fitzsimmons <fitzsim@redhat.com> - 0:2.7.6-3jpp_5fc
- Unstub docs.

* Sat Jul 22 2006 Jakub Jelinek <jakub@redhat.com> - 0:2.7.6-3jpp_4fc
- Remove hack-libgcj requirement.

* Fri Jul 21 2006 Thomas Fitzsimmons <fitzsim@redhat.com> - 0:2.7.6-3jpp_3fc
- Stub docs. (dist-fc6-java)
- Require hack-libgcj for build. (dist-fc6-java)
- Bump release number.

* Wed Jul 19 2006 Deepak Bhole <dbhole@redhat.com> = 0:2.7.6-3jpp_2fc
- From gbenson@redhat:
-   Omit the jedit subpackage to fix dependencies. 

* Wed Jul 19 2006 Deepak Bhole <dbhole@redhat.com> = 0:2.7.6-3jpp_1fc
- Added conditional native compilation.

* Fri Jan 13 2006 Fernando Nasser <fnasser@redhat.com> - 0:2.7.6-2jpp
- First JPP 1.7 build

* Fri Jan 13 2006 Fernando Nasser <fnasser@redhat.com> - 0:2.7.6-1jpp
- Update to 2.7.6.

* Fri Aug 20 2004 Ralph Apel <r.apel at r-apel.de> - 0:2.7.4-2jpp
- Build with ant-1.6.2.
- Made native scripts conditional

* Tue May 18 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:2.7.4-1jpp
- Update to 2.7.4.

* Fri Apr  2 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:2.7.3-2jpp
- Create alternatives also on upgrades.

* Wed Mar 31 2004 Ville Skyttä <ville.skytta at iki.fi> - 0:2.7.3-1jpp
- Update to 2.7.3.
- Include gcj build option and a native subpackage, build using
  "--with native" to get that.
- Add %{_bindir}/antlr alternative.

* Mon Dec 15 2003 Ville Skyttä <ville.skytta at iki.fi> - 0:2.7.2-3jpp
- Add non-versioned javadoc dir symlink.
- Crosslink with local J2SE javadocs.
- Spec cleanups, change to UTF-8.

* Sun Mar 30 2003 Ville Skyttä <ville.skytta at iki.fi> - 0:2.7.2-2jpp
- Rebuild for JPackage 1.5.

* Sat Mar  1 2003 Ville Skyttä <ville.skytta at iki.fi> - 2.7.2-1jpp
- Update to 2.7.2.
- Include antlr script and jEdit mode (see antlr-jedit RPM description).
- Use sed instead of bash 2 extension when symlinking jars during build.

* Tue May 07 2002 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.7.1-8jpp
- really section macro
- hardcoded distribution and vendor tag
- group tag again

* Thu May 2 2002 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.7.1-7jpp
- distribution tag
- group tag
- section macro

* Fri Jan 18 2002 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.7.1-6jpp
- versioned dir for javadoc
- no dependencies for manual and javadoc packages
- additional sources in individual archives

* Sat Dec 1 2001 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.7.1-5jpp
- javadoc in javadoc package

* Wed Nov 21 2001 Christian Zoffoli <czoffoli@littlepenguin.org> 2.7.1-4jpp
- removed packager tag
- new jpp extension

* Sat Oct 6 2001 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.7.1-3jpp
- used a build file instead of makefile
- build classes instead of blindly jared them !
- used original tarball
- corrected license spelling

* Sun Sep 30 2001 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.7.1-2jpp
- first unified release
- s/jPackage/JPackage

* Tue Aug 28 2001 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.7.1-1mdk
- first Mandrake release
