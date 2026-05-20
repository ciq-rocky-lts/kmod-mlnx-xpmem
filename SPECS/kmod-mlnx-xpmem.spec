# Kernel types to build for.  Use --without stock, --without clk6_12,
# --without clk6_18 on the rpmbuild line to disable specific kernel types.
# Use --without realtime to skip RT kernel variants.
%bcond_without stock
%bcond_with clk6_12
%bcond_with clk6_18
%bcond_without realtime

# CLK kernels only exist on RHEL 9
%if 0%{?rhel} != 9
%global with_clk6_12 0
%global with_clk6_18 0
%endif

# Save user's CLK intent before kernel version detection may undefine with_clk*.
# These flags gate BuildRequires so the kernel-devel packages are always pulled in.
%if %{with clk6_12}
%global want_clk6_12 1
%endif
%if %{with clk6_18}
%global want_clk6_18 1
%endif

# Detect kernel versions from installed kernel-devel packages.
# Each kernel type filters /usr/src/kernels/ for its own directories.
# Trim off any variant suffix (+rt, +64k).  If no kernel-devel found, default to epoch.
%if %{with stock}
%{!?kmod_stock_kver: %global kmod_stock_kver %(sh -c 'find /usr/src/kernels/* -maxdepth 0 -type d 2>/dev/null || date +"%%s"' | sort -V | grep -v '+clk' | tail -1 | awk -F '/' '{print $NF}' | sed 's/\.%{_arch}.*//')}
%endif

%if %{with clk6_12}
%{!?kmod_clk6_12_kver: %global kmod_clk6_12_kver %(sh -c 'find /usr/src/kernels/* -maxdepth 0 -type d 2>/dev/null || date +"%%s"' | sort -V | grep '+clk6\.12' | tail -1 | awk -F '/' '{print $NF}' | sed 's/\.%{_arch}.*//')}
# Disable CLK 6.12 if no kernel-devel found (e.g. during SRPM build).
# Top-level BuildRequires ensure the binary build fails if it's truly missing.
%if %(test -n "%{kmod_clk6_12_kver}" && echo 1 || echo 0) == 0
%undefine with_clk6_12
%endif
%endif

%if %{with clk6_18}
%{!?kmod_clk6_18_kver: %global kmod_clk6_18_kver %(sh -c 'find /usr/src/kernels/* -maxdepth 0 -type d 2>/dev/null || date +"%%s"' | sort -V | grep '+clk6\.18' | tail -1 | awk -F '/' '{print $NF}' | sed 's/\.%{_arch}.*//')}
# Disable CLK 6.18 if no kernel-devel found (e.g. during SRPM build).
# Top-level BuildRequires ensure the binary build fails if it's truly missing.
%if %(test -n "%{kmod_clk6_18_kver}" && echo 1 || echo 0) == 0
%undefine with_clk6_18
%endif
%endif

# Helper macros to extract kernel base version and release number from a kernel version string.
# Example: "5.14.0-503.5.1.el9_5" -> base "5.14.0", release "503"
%define kver_base() %(echo "%{1}" | grep -Eo '^.*-' | tr -d '-')
%define kver_release() %(echo "%{1}" | grep -Eo '\\-[[:digit:]]+\\.' | tr -d '.' | tr -d '-')

# For module signing: CLK kernels on RHEL 9 need stock kernel's sign-file
# (upstream 6.12.x sign-file uses OpenSSL 3 provider API; our PKCS11 config
# uses the OpenSSL 1.x engine API which the 5.14.0 sign-file still expects)
%if %{with clk6_12} || %{with clk6_18} || 0%{?is_clk_kernel}
%global sign_files_kernel_clk %(sh -c 'find /usr/src/kernels/* -maxdepth 0 -type d 2>/dev/null || date +"%%s"' | sort -V | awk -F '/' '{print $NF}' | grep -E '^5\.14|^4\.18' | tail -1 | sed 's/\.%{_arch}.*//')
%endif

# Information in description for secure-boot signed builds
%if 0%{?pe_signing_certkeyslot:1}
%define sb_summary "Signed for secure boot"
%else
%define sb_summary %{nil}
%endif

%global _use_internal_dependency_generator 0

Summary: Cross-partition memory
Name: kmod-mlnx-xpmem
Version: 2510.0.16
Release: 8%{?dist}
License: GPLv2 and LGPLv2.1
Url: http://www.mellanox.com/
Source: xpmem-%{version}.tar.gz
BuildRequires:  kmod
BuildRequires:  /usr/bin/perl

BuildRequires:  kernel-abi-stablelists
BuildRequires:  kernel-rpm-macros
BuildRequires:  redhat-rpm-config
BuildRequires:  systemd-rpm-macros
BuildRequires:  elfutils-libelf-devel
BuildRequires:  make,gcc,gcc-c++,glibc-devel,kernel-headers,tar,hostname,autoconf,automake,libtool

# Kernel-devel BuildRequires must be at the top level so the dependency
# resolver installs them before macro expansion detects kernel versions.
%if %{with stock}
BuildRequires:  kernel-devel
%ifnarch aarch64
BuildRequires:  kernel-debug-devel
%endif
%if 0%{?rhel} > 8
%if %{with realtime}
BuildRequires:  kernel-rt-devel
%ifnarch aarch64
BuildRequires:  kernel-rt-debug-devel
%endif
%endif
%ifarch aarch64
BuildRequires:  kernel-64k-devel
%if %{with realtime}
BuildRequires:  kernel-rt-64k-devel
%endif
%endif
%endif
%endif

%if 0%{?want_clk6_12}
BuildRequires:  kernel-clk6.12-devel
%ifnarch aarch64
BuildRequires:  kernel-clk6.12-debug-devel
%endif
%ifarch aarch64
%if 0%{?rhel} > 8
BuildRequires:  kernel-clk6.12-64k-devel
%endif
%endif
%if 0%{?rhel} < 10
# Secureboot workaround: CLK kernel sign-file uses OpenSSL 3 provider API;
# need stock kernel-devel for its sign-file which uses the engine API
BuildRequires:  kernel-devel < 5.15
%endif
%endif

%if 0%{?want_clk6_18}
BuildRequires:  kernel-clk6.18-devel
%ifnarch aarch64
BuildRequires:  kernel-clk6.18-debug-devel
%endif
%ifarch aarch64
%if 0%{?rhel} > 8
BuildRequires:  kernel-clk6.18-64k-devel
%endif
%endif
%if 0%{?rhel} < 10
# Secureboot workaround: CLK kernel sign-file uses OpenSSL 3 provider API;
# need stock kernel-devel for its sign-file which uses the engine API
BuildRequires:  kernel-devel < 5.15
%endif
%endif

%if 0%{?is_clk_kernel}
%if 0%{?rhel} < 10
# On CLK mock builders (is_clk_kernel=1) without an explicit --with clk6_12/18,
# the want_clk6_* flags are never set so the BR above is skipped.
# Pull in stock kernel-devel anyway so sign_files_kernel_clk can find its sign-file.
BuildRequires:  kernel-devel < 5.15
%endif
%endif

Source8000:     ciq_sbsign.macros
Source8001:     ciq_sb_kernel_driver.der
Source8002:     ciq_sb_kernel_driver_aarch64.der

%define __spec_install_post  /usr/lib/rpm/check-buildroot \
                             /usr/lib/rpm/redhat/brp-ldconfig \
                             /usr/lib/rpm/brp-compress \
                             /usr/lib/rpm/brp-strip-comment-note /usr/bin/strip /usr/bin/objdump \
                             /usr/lib/rpm/brp-strip-static-archive /usr/bin/strip \
                             PYTHON3="/usr/libexec/platform-python" /usr/lib/rpm/redhat/brp-mangle-shebangs

%define findpat %( echo "%""P" )
%define __find_requires /usr/lib/rpm/redhat/find-requires.ksyms
%define __find_provides /usr/lib/rpm/redhat/find-provides.ksyms %{kmod_name} %{?epoch:%{epoch}:}%{version}-%{release}
%define dup_state_dir %{_localstatedir}/lib/rpm-state/kmod-dups
%define kver_state_dir %{dup_state_dir}/kver
%define dup_module_list %{dup_state_dir}/rpm-%{name}-modules
%define debug_package %{nil}

Provides:       kmod-xpmem = %{version}
Obsoletes:      kmod-xpmem <= %{version}
# doca-ofed Requires: xpmem-dkms, so we have to provide this, even though it's not really dkms
Provides:       xpmem-dkms = %{version}
Obsoletes:      xpmem-dkms <= %{version}

ExcludeArch:    %{ix86}

# Boolean dependencies: install the right kmod subpackage for each installed kernel
Requires:       (%{name}-base if kernel)
Requires:       (%{name}-debug if kernel-debug)
Requires:       (%{name}-rt if kernel-rt)
Requires:       (%{name}-rt-debug if kernel-rt-debug)
Requires:       (%{name}-64k if kernel-64k)
Requires:       (%{name}-rt-64k if kernel-rt-64k)
Requires:       (%{name}-clk6.12-base if kernel-clk6.12)
Requires:       (%{name}-clk6.12-debug if kernel-clk6.12-debug)
Requires:       (%{name}-clk6.12-64k if kernel-clk6.12-64k)
Requires:       (%{name}-clk6.18-base if kernel-clk6.18)
Requires:       (%{name}-clk6.18-debug if kernel-clk6.18-debug)
Requires:       (%{name}-clk6.18-64k if kernel-clk6.18-64k)

# At least one variant subpackage must be installed
Requires:       (%{name}-base or %{name}-debug or %{name}-rt or %{name}-rt-debug or %{name}-64k or %{name}-rt-64k or %{name}-clk6.12-base or %{name}-clk6.12-debug or %{name}-clk6.12-64k or %{name}-clk6.18-base or %{name}-clk6.18-debug or %{name}-clk6.18-64k)


%description
This metapackage ensures the correct packages are installed for the
installed variants of the kernel.


# Parameterized macro for generating kmod variant subpackages.
# Named options:
#   -k  kernel package name (e.g. "kernel", "kernel-clk6.18")
#   -p  variant prefix for subpackage naming (omit for stock, "clk6.18-" for CLK)
#   -v  kernel version string
# Positional args:
#   %{1}  variant name (base, debug, rt, etc.)
#   %{2}  optional flag — if set, this is the "base" variant (no variant suffix on kernel name)
%define global_kmod_package(k:p:v:) %{expand:\
%package %{?-p:%{-p*}}%{1}
Summary:        Cross-partition memory

Requires:       %{name}-common
Requires:       %{-k*}%{!?2:-%{1}} >= %{kver_base %{-v*}}-%{kver_release %{-v*}}, %{-k*}%{!?2:-%{1}} < %{kver_base %{-v*}}-%(let release=%{kver_release %{-v*}}+1; echo $release)
Requires(post): %{_sbindir}/weak-modules
Requires(postun): %{_sbindir}/weak-modules

Recommends:     dnf-plugin-protected-kmods >= 1.0.0

%description %{?-p:%{-p*}}%{1}
This package provides XPMEM for the %{?-p:%{-p*}}%{1} kernel variant.

XPMEM is a Linux kernel module that enables a process to map the
memory of another process into its virtual address space.

This package includes the kernel module and associated tooling

This was built specifically for kernel series:
%{kver_base %{-v*}}-%{kver_release %{-v*}}
}

# Generate subpackages for stock kernel
%if %{with stock}
%global_kmod_package -k kernel -v %{kmod_stock_kver} base 1
%ifnarch aarch64
%global_kmod_package -k kernel -v %{kmod_stock_kver} debug
%endif
%if 0%{?rhel} > 8
%if %{with realtime}
%global_kmod_package -k kernel -v %{kmod_stock_kver} rt
%ifnarch aarch64
%global_kmod_package -k kernel -v %{kmod_stock_kver} rt-debug
%endif
%endif
%ifarch aarch64
%global_kmod_package -k kernel -v %{kmod_stock_kver} 64k
%if %{with realtime}
%global_kmod_package -k kernel -v %{kmod_stock_kver} rt-64k
%endif
%endif
%endif
%endif

# Generate subpackages for CLK 6.12 (no RT variants for CLK kernels)
%if %{with clk6_12}
%global_kmod_package -k kernel-clk6.12 -p clk6.12- -v %{kmod_clk6_12_kver} base 1
%ifnarch aarch64
%global_kmod_package -k kernel-clk6.12 -p clk6.12- -v %{kmod_clk6_12_kver} debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%global_kmod_package -k kernel-clk6.12 -p clk6.12- -v %{kmod_clk6_12_kver} 64k
%endif
%endif
%endif

# Generate subpackages for CLK 6.18 (no RT variants for CLK kernels)
%if %{with clk6_18}
%global_kmod_package -k kernel-clk6.18 -p clk6.18- -v %{kmod_clk6_18_kver} base 1
%ifnarch aarch64
%global_kmod_package -k kernel-clk6.18 -p clk6.18- -v %{kmod_clk6_18_kver} debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%global_kmod_package -k kernel-clk6.18 -p clk6.18- -v %{kmod_clk6_18_kver} 64k
%endif
%endif
%endif


%package common
Summary:        Cross-partition memory - Common Files
Requires:       grep
Requires:       procps
Requires:       module-init-tools
Requires:       lsof
Provides:       xpmem = %{version}
Obsoletes:      xpmem <= %{version}


%description common
XPMEM is a Linux kernel module that enables a process to map the
memory of another process into its virtual address space.

This package includes common utilities required by all kernel variant packages.


# set modules dir
%global install_mod_dir extra/%{name}

%{!?install_mod_dir: %global install_mod_dir updates}


%prep
%autosetup -n xpmem-%{version}
# Update source version to match RPM version
sed -i "s/AC_INIT(\[xpmem\], \[.*\]/AC_INIT([xpmem], [%{version}]/" configure.ac


%build
# Shell function to build one kernel variant.
# Args: $1=variant (-base, -debug, etc.), $2=kernel version, $3=prefix ("" or "clk6.18-"),
#       $4=kernel type suffix ("" or "+clk6.18")
BuildVariant() {
    local variant=$1
    local kver=$2
    local prefix=$3
    local ktype_suffix=$4
    local kvariant=$(echo "$variant" | sed 's/^-/+/g' | sed 's/^+base//g')
    kvariant="${ktype_suffix}${kvariant}"
    local builddir="../xpmem-%{version}-build-${prefix}${variant#-}"
    cp -a ../xpmem-%{version} "${builddir}/"
    cd "${builddir}"

    ./autogen.sh
    %{configure} \
      --with-module-prefix= \
      --with-kerneldir=%{_usrsrc}/kernels/${kver}.%{_arch}${kvariant} \
      $env \
      #
    %{make_build} SUBDIRS=kernel

    # Automatically generate dnf-plugin-protected-kmods config so we don't have to
    # bump versions in multiple places
    local pkgvariant="${prefix}${variant#-}"
    local variant_line=""
    if [ "${pkgvariant}" != "base" ]; then
        variant_line="variant = ${pkgvariant}"
    fi
    cat << EOF > protected-kmods-%{name}-${pkgvariant}.conf
[protected_kmods]
kmod_names = %{name}
${variant_line}
EOF
}

# Shell function to build all variants for a given kernel type.
# Args: $1=kernel version, $2=prefix, $3=build RT variants (0 or 1),
#       $4=kernel type suffix ("" or "+clk6.18")
# Unlike knem (which only gates 64k on arch), xpmem has inverted arch guards:
#   BUILD_DEBUG / BUILD_RT_DEBUG = 1 on x86_64, 0 on aarch64 (no -debug on aarch64)
#   BUILD_64K                    = 0 on x86_64, 1 on aarch64 (only on aarch64)
# These vars are set from RPM conditionals before calling this function.
BuildAllVariantsForKernel() {
    local kver=$1
    local prefix=$2
    local build_rt=$3
    local ktype_suffix=$4
    BuildVariant \-base "$kver" "$prefix" "$ktype_suffix"
    if [ "$BUILD_DEBUG" = "1" ]; then
        BuildVariant \-debug "$kver" "$prefix" "$ktype_suffix"
    fi
    if [ "$build_rt" = "1" ]; then
        BuildVariant \-rt "$kver" "$prefix" "$ktype_suffix"
        if [ "$BUILD_RT_DEBUG" = "1" ]; then
            BuildVariant \-rt-debug "$kver" "$prefix" "$ktype_suffix"
        fi
    fi
    if [ "$BUILD_64K" = "1" ]; then
        BuildVariant \-64k "$kver" "$prefix" "$ktype_suffix"
        if [ "$build_rt" = "1" ]; then
            BuildVariant \-rt-64k "$kver" "$prefix" "$ktype_suffix"
        fi
    fi
}

# xpmem: debug and rt-debug only on non-aarch64; 64k and rt-64k only on aarch64
export BUILD_DEBUG=1
export BUILD_RT_DEBUG=1
export BUILD_RT=0
export BUILD_64K=0
%ifarch aarch64
export BUILD_DEBUG=0
export BUILD_RT_DEBUG=0
%if 0%{?rhel} > 8
export BUILD_64K=1
%endif
%endif
%if 0%{?rhel} > 8 && %{with realtime}
export BUILD_RT=1
%endif

%if %{with stock}
BuildAllVariantsForKernel "%{kmod_stock_kver}" "" "$BUILD_RT" ""
%endif
%if %{with clk6_12}
BuildAllVariantsForKernel "%{kmod_clk6_12_kver}" "clk6.12-" "0" "+clk6.12"
%endif
%if %{with clk6_18}
BuildAllVariantsForKernel "%{kmod_clk6_18_kver}" "clk6.18-" "0" "+clk6.18"
%endif


%install
%if %{?_with_modsign:1}%{!?_with_modsign:0}
%include %{SOURCE8000}
# If the module signing keys are not defined, define them here.
%{!?privkey: %define privkey %{_sysconfdir}/pki/SECURE-BOOT-KEY.priv}
%{!?pubkey: %define pubkey %{_sysconfdir}/pki/SECURE-BOOT-KEY.der}
%endif

# Shell function to install one kernel variant.
# Args: $1=variant, $2=kernel version, $3=prefix, $4=sign-file kernel version,
#       $5=kernel type suffix ("" or "+clk6.18")
InstallVariant() {
    local variant=$1
    local kver=$2
    local prefix=$3
    local sign_kver=$4
    local ktype_suffix=$5
    local kvariant=$(echo "$variant" | sed 's/^-/+/g' | sed 's/^+base//g')
    kvariant="${ktype_suffix}${kvariant}"
    local builddir="../xpmem-%{version}-build-${prefix}${variant#-}"
    local pkgvariant="${prefix}${variant#-}"

    # Let's copy any config files we need (hopefully temporarily)
    if [ -e "yubihsm_pkcs11.conf" ]; then
        cp -a yubihsm_pkcs11.conf "${builddir}/"
    fi

    cd "${builddir}"

    export INSTALL_MOD_DIR=%{install_mod_dir}
    export LIB_MOD_DIR=/lib/modules/${kver}.%{_arch}${kvariant}/$INSTALL_MOD_DIR
    %{make_install} moduledir=$LIB_MOD_DIR SUBDIRS=kernel

    # Only install common files for base variant
    rm -rf %{buildroot}/%{_libdir}/libxpmem.la
    rm -rf %{buildroot}/etc/init.d/xpmem
    rm -f %{buildroot}/usr/lib*/pkgconfig/cray-xpmem.pc
    if [ "$variant" == "-base" ] && [ "${COMMON_INSTALLED:-0}" == "0" ]; then
        mkdir -p %{buildroot}%{_prefix}/lib/modules-load.d
        echo "xpmem" >%{buildroot}%{_prefix}/lib/modules-load.d/xpmem.conf
        mv %{buildroot}/lib/udev %{buildroot}%{_prefix}/lib/udev
        export COMMON_INSTALLED=1
    else
        rm -rf %{buildroot}/lib/udev
    fi

    %{__install} -d %{buildroot}%{_sysconfdir}/depmod.d/
    for module in $(find %{buildroot}/lib/modules/${kver}.%{_arch}${kvariant} -name '*.ko' -o -name '*.ko.gz' 2>/dev/null | sort)
    do
        ko_name=${module##*/}
        mod_name=${ko_name/.ko*/}
        mod_path=${module/*%{name}}
        mod_path=${mod_path/\/$ko_name}
        echo "override $mod_name * weak-updates/%{name}$mod_path" >> %{buildroot}%{_sysconfdir}/depmod.d/%{name}-$mod_name.conf
        echo "override $mod_name * extra/%{name}$mod_path" >> %{buildroot}%{_sysconfdir}/depmod.d/%{name}-$mod_name.conf
    done

    # strip the modules(s)
    find %{buildroot}/lib/modules/${kver}.%{_arch}${kvariant} -name \*.ko -type f 2>/dev/null | xargs --no-run-if-empty %{__strip} --strip-debug

    # Sign the modules(s)
    %if %{?_with_modsign:1}%{!?_with_modsign:0}
    for module in $(find %{buildroot}/lib/modules/${kver}.%{_arch}${kvariant} -type f -name \*.ko 2>/dev/null); do
        for attempt in 1 2 3; do
            errmsg=$(%{_usrsrc}/kernels/${sign_kver}.%{_arch}/scripts/sign-file \
                sha256 %{privkey} %{pubkey} $module 2>&1) && rc=0 || rc=$?
            [ $rc -eq 0 ] && break
            if [ $attempt -lt 3 ] && echo "$errmsg" | grep -q "All sessions are allocated"; then
                echo "HSM session limit hit, sleeping 30s before retry (attempt $attempt/3)..." >&2
                sleep 30
            else
                echo "$errmsg" >&2
                exit $rc
            fi
        done
        sleep %{?kmod_sign_sleep}%{!?kmod_sign_sleep:4}
    done
    %endif

    %{__install} -m 0644 protected-kmods-%{name}-${pkgvariant}.conf -D %{buildroot}%{_sysconfdir}/dnf/plugins/protected-kmods.d/%{name}-${pkgvariant}.conf
}

# Shell function to install all variants for a given kernel type.
# Args: $1=kernel version, $2=prefix, $3=sign-file kernel version, $4=build RT variants (0 or 1),
#       $5=kernel type suffix ("" or "+clk6.18")
# Unlike knem (which only gates 64k on arch), xpmem has inverted arch guards:
#   BUILD_DEBUG / BUILD_RT_DEBUG = 1 on x86_64, 0 on aarch64 (no -debug on aarch64)
#   BUILD_64K                    = 0 on x86_64, 1 on aarch64 (only on aarch64)
# These vars are set from RPM conditionals before calling this function.
InstallAllVariantsForKernel() {
    local kver=$1
    local prefix=$2
    local sign_kver=$3
    local build_rt=$4
    local ktype_suffix=$5
    InstallVariant \-base "$kver" "$prefix" "$sign_kver" "$ktype_suffix"
    if [ "$BUILD_DEBUG" = "1" ]; then
        InstallVariant \-debug "$kver" "$prefix" "$sign_kver" "$ktype_suffix"
    fi
    if [ "$build_rt" = "1" ]; then
        InstallVariant \-rt "$kver" "$prefix" "$sign_kver" "$ktype_suffix"
        if [ "$BUILD_RT_DEBUG" = "1" ]; then
            InstallVariant \-rt-debug "$kver" "$prefix" "$sign_kver" "$ktype_suffix"
        fi
    fi
    if [ "$BUILD_64K" = "1" ]; then
        InstallVariant \-64k "$kver" "$prefix" "$sign_kver" "$ktype_suffix"
        if [ "$build_rt" = "1" ]; then
            InstallVariant \-rt-64k "$kver" "$prefix" "$sign_kver" "$ktype_suffix"
        fi
    fi
}

# xpmem: debug and rt-debug only on non-aarch64; 64k and rt-64k only on aarch64
export BUILD_DEBUG=1
export BUILD_RT_DEBUG=1
export BUILD_RT=0
export BUILD_64K=0
%ifarch aarch64
export BUILD_DEBUG=0
export BUILD_RT_DEBUG=0
%if 0%{?rhel} > 8
export BUILD_64K=1
%endif
%endif
%if 0%{?rhel} > 8 && %{with realtime}
export BUILD_RT=1
%endif

%if %{with stock}
%if 0%{?is_clk_kernel}
InstallAllVariantsForKernel "%{kmod_stock_kver}" "" "%{sign_files_kernel_clk}" "$BUILD_RT" ""
%else
InstallAllVariantsForKernel "%{kmod_stock_kver}" "" "%{kmod_stock_kver}" "$BUILD_RT" ""
%endif
%endif
%if %{with clk6_12}
InstallAllVariantsForKernel "%{kmod_clk6_12_kver}" "clk6.12-" "%{sign_files_kernel_clk}" "0" "+clk6.12"
%endif
%if %{with clk6_18}
InstallAllVariantsForKernel "%{kmod_clk6_18_kver}" "clk6.18-" "%{sign_files_kernel_clk}" "0" "+clk6.18"
%endif


# Named options:
#   -p  variant prefix (omit for stock)
#   -v  kernel version string
#   -s  kernel type suffix (omit for stock, "+clk6.18" for CLK)
# Positional: %{1}=variant, %{2}=optional base flag
%define post_scriptlet(p:v:s:) %{expand:\
%post %{?-p:%{-p*}}%{1}
modules=( $(find /lib/modules/%{-v*}.%{_arch}%{?-s:%{-s*}}%{!?2:+%{1}}/extra/%{name}/ | grep '\\.ko$') )
printf '%s\\n' "${modules[@]}" | %{_sbindir}/weak-modules --add-modules

mkdir -p "%{kver_state_dir}"
touch "%{kver_state_dir}/%{-v*}.%{_arch}-%{?-p:%{-p*}}%{1}"
}

# Stock kernel post scriptlets
%if %{with stock}
%post_scriptlet -v %{kmod_stock_kver} base 1
%ifnarch aarch64
%post_scriptlet -v %{kmod_stock_kver} debug
%endif
%if 0%{?rhel} > 8
%if %{with realtime}
%post_scriptlet -v %{kmod_stock_kver} rt
%ifnarch aarch64
%post_scriptlet -v %{kmod_stock_kver} rt-debug
%endif
%endif
%ifarch aarch64
%post_scriptlet -v %{kmod_stock_kver} 64k
%if %{with realtime}
%post_scriptlet -v %{kmod_stock_kver} rt-64k
%endif
%endif
%endif
%endif

# CLK 6.12 kernel post scriptlets
%if %{with clk6_12}
%post_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 base 1
%ifnarch aarch64
%post_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%post_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 64k
%endif
%endif
%endif

# CLK 6.18 kernel post scriptlets
%if %{with clk6_18}
%post_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 base 1
%ifnarch aarch64
%post_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%post_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 64k
%endif
%endif
%endif


%define posttrans_scriptlet(p:v:s:) %{expand:\
%posttrans %{?-p:%{-p*}}%{1}
if [ -f "%{kver_state_dir}/%{-v*}.%{_arch}-%{?-p:%{-p*}}%{1}" ]; then
    rm -f "%{kver_state_dir}/%{-v*}.%{_arch}-%{?-p:%{-p*}}%{1}"
    rmdir "%{kver_state_dir}" 2>/dev/null
fi

rmdir "%{dup_state_dir}" 2>/dev/null
exit 0
}

# Stock kernel posttrans scriptlets
%if %{with stock}
%posttrans_scriptlet -v %{kmod_stock_kver} base
%ifnarch aarch64
%posttrans_scriptlet -v %{kmod_stock_kver} debug
%endif
%if 0%{?rhel} > 8
%if %{with realtime}
%posttrans_scriptlet -v %{kmod_stock_kver} rt
%ifnarch aarch64
%posttrans_scriptlet -v %{kmod_stock_kver} rt-debug
%endif
%endif
%ifarch aarch64
%posttrans_scriptlet -v %{kmod_stock_kver} 64k
%if %{with realtime}
%posttrans_scriptlet -v %{kmod_stock_kver} rt-64k
%endif
%endif
%endif
%endif

# CLK 6.12 kernel posttrans scriptlets
%if %{with clk6_12}
%posttrans_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 base
%ifnarch aarch64
%posttrans_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%posttrans_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 64k
%endif
%endif
%endif

# CLK 6.18 kernel posttrans scriptlets
%if %{with clk6_18}
%posttrans_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 base
%ifnarch aarch64
%posttrans_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%posttrans_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 64k
%endif
%endif
%endif


%define preun_scriptlet(p:v:s:) %{expand:\
%preun %{?-p:%{-p*}}%{1}
if rpm -q --filetriggers kmod 2>/dev/null | grep -q "Trigger for weak-modules call on kmod removal"; then
    mkdir -p "%{kver_state_dir}"
    touch "%{kver_state_dir}/%{-v*}.%{_arch}-%{?-p:%{-p*}}%{1}"
fi

mkdir -p "%{dup_state_dir}"
rpm -ql %{name}-%{?-p:%{-p*}}%{1}-%{version}-%{release}.%{_arch} | grep '\\.ko$' > "%{dup_module_list}-%{?-p:%{-p*}}%{1}"
}

# Stock kernel preun scriptlets
%if %{with stock}
%preun_scriptlet -v %{kmod_stock_kver} base
%ifnarch aarch64
%preun_scriptlet -v %{kmod_stock_kver} debug
%endif
%if 0%{?rhel} > 8
%if %{with realtime}
%preun_scriptlet -v %{kmod_stock_kver} rt
%ifnarch aarch64
%preun_scriptlet -v %{kmod_stock_kver} rt-debug
%endif
%endif
%ifarch aarch64
%preun_scriptlet -v %{kmod_stock_kver} 64k
%if %{with realtime}
%preun_scriptlet -v %{kmod_stock_kver} rt-64k
%endif
%endif
%endif
%endif

# CLK 6.12 kernel preun scriptlets
%if %{with clk6_12}
%preun_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 base
%ifnarch aarch64
%preun_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%preun_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 64k
%endif
%endif
%endif

# CLK 6.18 kernel preun scriptlets
%if %{with clk6_18}
%preun_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 base
%ifnarch aarch64
%preun_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%preun_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 64k
%endif
%endif
%endif


%define postun_scriptlet(p:v:s:) %{expand:\
%postun %{?-p:%{-p*}}%{1}
if rpm -q --filetriggers kmod 2>/dev/null | grep -q "Trigger for weak-modules call on kmod removal"; then
    initramfs_opt="--no-initramfs"
else
    initramfs_opt=""
fi

modules=( $(cat "%{dup_module_list}-%{?-p:%{-p*}}%{1}") )
rm -f "%{dup_module_list}-%{?-p:%{-p*}}%{1}"
printf '%s\\n' "${modules[@]}" | %{_sbindir}/weak-modules --remove-modules $initramfs_opt

rmdir "%{dup_state_dir}" 2>/dev/null

exit 0
}

# Stock kernel postun scriptlets
%if %{with stock}
%postun_scriptlet -v %{kmod_stock_kver} base
%ifnarch aarch64
%postun_scriptlet -v %{kmod_stock_kver} debug
%endif
%if 0%{?rhel} > 8
%if %{with realtime}
%postun_scriptlet -v %{kmod_stock_kver} rt
%ifnarch aarch64
%postun_scriptlet -v %{kmod_stock_kver} rt-debug
%endif
%endif
%ifarch aarch64
%postun_scriptlet -v %{kmod_stock_kver} 64k
%if %{with realtime}
%postun_scriptlet -v %{kmod_stock_kver} rt-64k
%endif
%endif
%endif
%endif

# CLK 6.12 kernel postun scriptlets
%if %{with clk6_12}
%postun_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 base
%ifnarch aarch64
%postun_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%postun_scriptlet -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 64k
%endif
%endif
%endif

# CLK 6.18 kernel postun scriptlets
%if %{with clk6_18}
%postun_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 base
%ifnarch aarch64
%postun_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%postun_scriptlet -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 64k
%endif
%endif
%endif


%files


%files common
%license COPYING COPYING.LESSER
%doc AUTHORS NEWS
%defattr(644,root,root,755)
%{_prefix}/lib/modules-load.d/xpmem.conf
%{_prefix}/lib/udev/rules.d/*-xpmem.rules
%config %{_sysconfdir}/depmod.d/%{name}*


# Named options:
#   -p  variant prefix (omit for stock)
#   -v  kernel version string
#   -s  kernel type suffix (omit for stock, "+clk6.18" for CLK)
# Positional: %{1}=variant, %{2}=optional base flag
%define global_files(p:v:s:) %{expand:\
%files %{?-p:%{-p*}}%{1}
%defattr(644,root,root,755)
/lib/modules/%{-v*}.%{_arch}%{?-s:%{-s*}}%{!?2:+%{1}}/
%config %{_sysconfdir}/dnf/plugins/protected-kmods.d/%{name}-%{?-p:%{-p*}}%{1}.conf
}

# Stock kernel files
%if %{with stock}
%global_files -v %{kmod_stock_kver} base 1
%ifnarch aarch64
%global_files -v %{kmod_stock_kver} debug
%endif
%if 0%{?rhel} > 8
%if %{with realtime}
%global_files -v %{kmod_stock_kver} rt
%ifnarch aarch64
%global_files -v %{kmod_stock_kver} rt-debug
%endif
%endif
%ifarch aarch64
%global_files -v %{kmod_stock_kver} 64k
%if %{with realtime}
%global_files -v %{kmod_stock_kver} rt-64k
%endif
%endif
%endif
%endif

# CLK 6.12 kernel files
%if %{with clk6_12}
%global_files -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 base 1
%ifnarch aarch64
%global_files -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%global_files -p clk6.12- -v %{kmod_clk6_12_kver} -s +clk6.12 64k
%endif
%endif
%endif

# CLK 6.18 kernel files
%if %{with clk6_18}
%global_files -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 base 1
%ifnarch aarch64
%global_files -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 debug
%endif
%if 0%{?rhel} > 8
%ifarch aarch64
%global_files -p clk6.18- -v %{kmod_clk6_18_kver} -s +clk6.18 64k
%endif
%endif
%endif


%changelog
* Mon May 11 2026 Joseph S. Tate <jtate@ciq.com> - 2510.0.16-8
- Bump for CLK 6.12.87 and 6.18.28 kernel builds

* Tue May 05 2026 Joseph S. Tate <jtate@ciq.com> - 2510.0.16-7
- Bump for CLK 6.12.85 kernel rebuild

* Wed Apr 29 2026 Joseph S. Tate <jtate@ciq.com> - 2510.0.16-6
- Bump for clk6_18 build

* Tue Apr 28 2026 Joseph Tate <jtate@ciq.com> - 2510.0.16-5
- Use opt-in %%bcond_with for clk6_12 and clk6_18 (default: stock only)
- Fix sign_files_kernel_clk guard to also cover is_clk_kernel builds
- On CLK builders, use 5.14.0 stock sign-file for stock variant (CLK sign-file
  uses OpenSSL 3 provider API; our PKCS11 config uses the OpenSSL 1.x engine API)
- Guard %%include of ciq_sbsign.macros under _with_modsign
- Add BuildRequires kernel-devel < 5.15 under is_clk_kernel guard

* Tue Apr 14 2026 David Gomez <dgomez@ciq.com> - 2510.0.16-4
- Build for all kernel types (stock, CLK 6.12, CLK 6.18) in a single spec
- Replace is_clk_kernel flag with --without stock/clk6_12/clk6_18 bcond flags
- Auto-detect kernel versions per type from /usr/src/kernels/ using +clk suffix
- Parameterize all RPM macros with named options (k:p:v:s:) for multi-kernel support
- Add BuildAllVariantsForKernel/InstallAllVariantsForKernel shell wrappers
- Preserve xpmem arch guards: debug/rt-debug on non-aarch64, 64k/rt-64k on aarch64
- CLK kernels auto-disabled on non-RHEL-9
- CLK signing uses stock kernel's sign-file (openssl3-engines workaround)
- Move kernel-devel BuildRequires to top-level preamble

* Wed Mar 11 2026 Jonathan Dieter <jdieter@ciq.com> - 2510.0.16-3
- Bump release for new kernel

* Wed Feb 11 2026 Jonathan Dieter <jdieter@ciq.com> - 2510.0.16-2
- Bump release for new kernel

* Fri Nov 21 2025 Jonathan Dieter <jdieter@ciq.com> - 2510.0.16-1
- Update for new Mellanox release

* Fri Nov 14 2025 Jonathan Dieter <jdieter@ciq.com> - 2.7.4-9
- Add support for all the different kernel variants
- Add metapackage to ensure the correct kmod variant is installed for any
  installed kernel variant

* Thu Aug 07 2025 Jonathan Dieter <jdieter@ciq.com> - 2.7.4-8
- Ensure initramfs is rebuilt when installing kmod

* Fri Jun 20 2025 Skip Grube <sgrube@ciq.com> - 2.7.4-7
- Bump for CLK kernel rebuild

* Fri Jun 13 2025 Jonathan Dieter <jdieter@ciq.com> - 2.7.4-6
- Ensure sign-file workaround is only applied to Rocky < 10
- Remove unused python generators

* Mon Jun 09 2025 Skip Grube <sgrube@ciq.com> - 2.7.4-5
- Add sign-file workaround to enable secureboot signing for newer kernels

* Fri Mar 14 2025 Jonathan Dieter <jdieter@ciq.com> - 2.7.4-4
- Fix SecureBoot macro

* Wed Mar 12 2025 Jonathan Dieter <jdieter@ciq.com> - 2.7.4-3
- Add SecureBoot config

* Tue Mar 11 2025 Jonathan Dieter <jdieter@ciq.com> - 2.7.4-2
- Initial rebuild for Rocky
