class Bzip2 < Formula
  desc "Freely available high-quality data compressor"
  homepage "https://sourceware.org/bzip2/"
  url "https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz"
  sha256 "ab5a03176ee106d3f0fa90e381da478ddae405918153cca248e682cd0c4a2269"
  license "bzip2-1.0.6"

  livecheck do
    url "https://sourceware.org/pub/bzip2/"
    regex(/href=.*?bzip2[._-]v?(\d+(?:\.\d+)+)\.t/i)
  end

  keg_only :provided_by_macos

  def install
    inreplace "Makefile", "$(PREFIX)/man", "$(PREFIX)/share/man"

    system "make", "install", "PREFIX=#{prefix}"

    on_linux do
      # Install shared libraries
      system "make", "-f", "Makefile-libbz2_so", "clean"
      system "make", "-f", "Makefile-libbz2_so"
      lib.install "libbz2.so.#{version}", "libbz2.so.#{version.major_minor}"
      lib.install_symlink "libbz2.so.#{version}" => "libbz2.so.#{version.major}"
      lib.install_symlink "libbz2.so.#{version}" => "libbz2.so"
    end
  end

  test do
    testfilepath = testpath + "sample_in.txt"
    zipfilepath = testpath + "sample_in.txt.bz2"

    testfilepath.write "TEST CONTENT"

    system "#{bin}/bzip2", testfilepath
    system "#{bin}/bunzip2", zipfilepath

    assert_equal "TEST CONTENT", testfilepath.read
  end
end
