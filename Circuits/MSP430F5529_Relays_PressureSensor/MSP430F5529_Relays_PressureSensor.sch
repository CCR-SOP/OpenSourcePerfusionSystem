<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE eagle SYSTEM "eagle.dtd">
<eagle version="9.3.2">
<drawing>
<settings>
<setting alwaysvectorfont="no"/>
<setting verticaltext="up"/>
</settings>
<grid distance="0.1" unitdist="inch" unit="inch" style="lines" multiple="1" display="no" altdistance="0.01" altunitdist="inch" altunit="inch"/>
<layers>
<layer number="1" name="Top" color="4" fill="1" visible="no" active="no"/>
<layer number="2" name="Route2" color="1" fill="3" visible="no" active="no"/>
<layer number="3" name="Route3" color="4" fill="3" visible="no" active="no"/>
<layer number="4" name="Route4" color="1" fill="4" visible="no" active="no"/>
<layer number="5" name="Route5" color="4" fill="4" visible="no" active="no"/>
<layer number="6" name="Route6" color="1" fill="8" visible="no" active="no"/>
<layer number="7" name="Route7" color="4" fill="8" visible="no" active="no"/>
<layer number="8" name="Route8" color="1" fill="2" visible="no" active="no"/>
<layer number="9" name="Route9" color="4" fill="2" visible="no" active="no"/>
<layer number="10" name="Route10" color="1" fill="7" visible="no" active="no"/>
<layer number="11" name="Route11" color="4" fill="7" visible="no" active="no"/>
<layer number="12" name="Route12" color="1" fill="5" visible="no" active="no"/>
<layer number="13" name="Route13" color="4" fill="5" visible="no" active="no"/>
<layer number="14" name="Route14" color="1" fill="6" visible="no" active="no"/>
<layer number="15" name="Route15" color="4" fill="6" visible="no" active="no"/>
<layer number="16" name="Bottom" color="1" fill="1" visible="no" active="no"/>
<layer number="17" name="Pads" color="2" fill="1" visible="no" active="no"/>
<layer number="18" name="Vias" color="2" fill="1" visible="no" active="no"/>
<layer number="19" name="Unrouted" color="6" fill="1" visible="no" active="no"/>
<layer number="20" name="Dimension" color="15" fill="1" visible="no" active="no"/>
<layer number="21" name="tPlace" color="7" fill="1" visible="no" active="no"/>
<layer number="22" name="bPlace" color="7" fill="1" visible="no" active="no"/>
<layer number="23" name="tOrigins" color="15" fill="1" visible="no" active="no"/>
<layer number="24" name="bOrigins" color="15" fill="1" visible="no" active="no"/>
<layer number="25" name="tNames" color="7" fill="1" visible="no" active="no"/>
<layer number="26" name="bNames" color="7" fill="1" visible="no" active="no"/>
<layer number="27" name="tValues" color="7" fill="1" visible="no" active="no"/>
<layer number="28" name="bValues" color="7" fill="1" visible="no" active="no"/>
<layer number="29" name="tStop" color="7" fill="3" visible="no" active="no"/>
<layer number="30" name="bStop" color="7" fill="6" visible="no" active="no"/>
<layer number="31" name="tCream" color="7" fill="4" visible="no" active="no"/>
<layer number="32" name="bCream" color="7" fill="5" visible="no" active="no"/>
<layer number="33" name="tFinish" color="6" fill="3" visible="no" active="no"/>
<layer number="34" name="bFinish" color="6" fill="6" visible="no" active="no"/>
<layer number="35" name="tGlue" color="7" fill="4" visible="no" active="no"/>
<layer number="36" name="bGlue" color="7" fill="5" visible="no" active="no"/>
<layer number="37" name="tTest" color="7" fill="1" visible="no" active="no"/>
<layer number="38" name="bTest" color="7" fill="1" visible="no" active="no"/>
<layer number="39" name="tKeepout" color="4" fill="11" visible="no" active="no"/>
<layer number="40" name="bKeepout" color="1" fill="11" visible="no" active="no"/>
<layer number="41" name="tRestrict" color="4" fill="10" visible="no" active="no"/>
<layer number="42" name="bRestrict" color="1" fill="10" visible="no" active="no"/>
<layer number="43" name="vRestrict" color="2" fill="10" visible="no" active="no"/>
<layer number="44" name="Drills" color="7" fill="1" visible="no" active="no"/>
<layer number="45" name="Holes" color="7" fill="1" visible="no" active="no"/>
<layer number="46" name="Milling" color="3" fill="1" visible="no" active="no"/>
<layer number="47" name="Measures" color="7" fill="1" visible="no" active="no"/>
<layer number="48" name="Document" color="7" fill="1" visible="no" active="no"/>
<layer number="49" name="Reference" color="7" fill="1" visible="no" active="no"/>
<layer number="51" name="tDocu" color="6" fill="1" visible="no" active="no"/>
<layer number="52" name="bDocu" color="7" fill="1" visible="no" active="no"/>
<layer number="88" name="SimResults" color="9" fill="1" visible="yes" active="yes"/>
<layer number="89" name="SimProbes" color="9" fill="1" visible="yes" active="yes"/>
<layer number="90" name="Modules" color="5" fill="1" visible="yes" active="yes"/>
<layer number="91" name="Nets" color="2" fill="1" visible="yes" active="yes"/>
<layer number="92" name="Busses" color="1" fill="1" visible="yes" active="yes"/>
<layer number="93" name="Pins" color="2" fill="1" visible="no" active="yes"/>
<layer number="94" name="Symbols" color="4" fill="1" visible="yes" active="yes"/>
<layer number="95" name="Names" color="7" fill="1" visible="yes" active="yes"/>
<layer number="96" name="Values" color="7" fill="1" visible="yes" active="yes"/>
<layer number="97" name="Info" color="7" fill="1" visible="yes" active="yes"/>
<layer number="98" name="Guide" color="6" fill="1" visible="yes" active="yes"/>
</layers>
<schematic xreflabel="%F%N/%S.%C%R" xrefpart="/%S.%C%R">
<libraries>
<library name="relay" urn="urn:adsk.eagle:library:339">
<description>&lt;b&gt;Relays&lt;/b&gt;&lt;p&gt;
&lt;ul&gt;
&lt;li&gt;Eichhoff
&lt;li&gt;Finder
&lt;li&gt;Fujitsu
&lt;li&gt;HAMLIN
&lt;li&gt;OMRON
&lt;li&gt;Matsushita
&lt;li&gt;NAiS
&lt;li&gt;Siemens
&lt;li&gt;Schrack
&lt;/ul&gt;
&lt;author&gt;Created by librarian@cadsoft.de&lt;/author&gt;</description>
<packages>
<package name="DIL06" urn="urn:adsk.eagle:footprint:24037/1" library_version="1">
<description>&lt;b&gt;Dual In Line Package&lt;/b&gt;</description>
<wire x1="4.31" y1="3.121" x2="-4.31" y2="3.121" width="0.1524" layer="21"/>
<wire x1="-4.31" y1="-3.096" x2="4.31" y2="-3.096" width="0.1524" layer="21"/>
<wire x1="4.31" y1="3.121" x2="4.31" y2="-3.096" width="0.1524" layer="21"/>
<wire x1="-4.31" y1="3.121" x2="-4.31" y2="1.016" width="0.1524" layer="21"/>
<wire x1="-4.31" y1="-3.096" x2="-4.31" y2="-1.016" width="0.1524" layer="21"/>
<wire x1="-4.31" y1="1.016" x2="-4.31" y2="-1.016" width="0.1524" layer="21" curve="-180"/>
<pad name="1" x="-2.54" y="-3.81" drill="0.8128" shape="long" rot="R90"/>
<pad name="2" x="0" y="-3.81" drill="0.8128" shape="long" rot="R90"/>
<pad name="5" x="0" y="3.81" drill="0.8128" shape="long" rot="R90"/>
<pad name="6" x="-2.54" y="3.81" drill="0.8128" shape="long" rot="R90"/>
<pad name="3" x="2.54" y="-3.81" drill="0.8128" shape="long" rot="R90"/>
<pad name="4" x="2.54" y="3.81" drill="0.8128" shape="long" rot="R90"/>
<text x="-2.413" y="-0.635" size="1.27" layer="27" ratio="10">&gt;VALUE</text>
<text x="-4.564" y="-2.921" size="1.27" layer="25" ratio="10" rot="R90">&gt;NAME</text>
</package>
<package name="DIL06SMD" urn="urn:adsk.eagle:footprint:24038/1" library_version="1">
<description>&lt;b&gt;DIL06 SMD&lt;/b&gt; NAiS&lt;p&gt;
Source: http://www.mew-europe.com/..  pti_en.pdf</description>
<wire x1="-4.31" y1="-3.144" x2="4.31" y2="-3.144" width="0.1524" layer="21"/>
<wire x1="4.31" y1="-3.144" x2="4.31" y2="3.144" width="0.1524" layer="21"/>
<wire x1="4.31" y1="3.144" x2="-4.31" y2="3.144" width="0.1524" layer="21"/>
<wire x1="-4.31" y1="3.144" x2="-4.31" y2="-3.144" width="0.1524" layer="21"/>
<circle x="-2.57" y="-1.8" radius="0.6" width="0" layer="21"/>
<smd name="1" x="-2.54" y="-4.15" dx="1.5" dy="1.9" layer="1"/>
<smd name="2" x="0" y="-4.15" dx="1.5" dy="1.9" layer="1"/>
<smd name="3" x="2.54" y="-4.15" dx="1.5" dy="1.9" layer="1"/>
<smd name="4" x="2.54" y="4.15" dx="1.5" dy="1.9" layer="1"/>
<smd name="5" x="0" y="4.15" dx="1.5" dy="1.9" layer="1"/>
<smd name="6" x="-2.54" y="4.15" dx="1.5" dy="1.9" layer="1"/>
<text x="-4.9164" y="-3.175" size="1.397" layer="25" ratio="10" rot="R90">&gt;NAME</text>
<text x="6.2626" y="-3.175" size="1.397" layer="27" ratio="10" rot="R90">&gt;VALUE</text>
<rectangle x1="-0.508" y1="-4.572" x2="0.508" y2="-3.175" layer="51"/>
<rectangle x1="-3.048" y1="-4.572" x2="-2.032" y2="-3.175" layer="51"/>
<rectangle x1="2.032" y1="-4.572" x2="3.048" y2="-3.175" layer="51"/>
<rectangle x1="2.032" y1="3.175" x2="3.048" y2="4.572" layer="51"/>
<rectangle x1="-0.508" y1="3.175" x2="0.508" y2="4.572" layer="51"/>
<rectangle x1="-3.048" y1="3.175" x2="-2.032" y2="4.572" layer="51"/>
</package>
<package name="SOP06" urn="urn:adsk.eagle:footprint:24039/1" library_version="1">
<description>&lt;b&gt;SOP6 - AQV21, AQV22, AQV41&lt;/b&gt; Sereis NAiS&lt;p&gt;Source: http://www.mew-europe.com/..  pti_en.pdf</description>
<wire x1="-3.27" y1="2.075" x2="3.27" y2="2.075" width="0.254" layer="21"/>
<wire x1="3.27" y1="2.075" x2="3.27" y2="-2.075" width="0.254" layer="21"/>
<wire x1="3.27" y1="-2.075" x2="-3.27" y2="-2.075" width="0.254" layer="21"/>
<wire x1="-3.27" y1="-2.075" x2="-3.27" y2="2.075" width="0.254" layer="21"/>
<circle x="-2.54" y="-1.524" radius="0.254" width="0" layer="21"/>
<smd name="1" x="-2.54" y="-3" dx="0.8" dy="1.2" layer="1"/>
<smd name="2" x="0" y="-3" dx="0.8" dy="1.2" layer="1"/>
<smd name="3" x="2.54" y="-3" dx="0.8" dy="1.2" layer="1"/>
<smd name="4" x="2.54" y="3" dx="0.8" dy="1.2" layer="1"/>
<smd name="5" x="0" y="3" dx="0.8" dy="1.2" layer="1"/>
<smd name="6" x="-2.54" y="3" dx="0.8" dy="1.2" layer="1"/>
<text x="-3.81" y="-2.54" size="1.27" layer="25" rot="R90">&gt;NAME</text>
<text x="5.08" y="-2.54" size="1.27" layer="27" rot="R90">&gt;VALUE</text>
<rectangle x1="-2.77" y1="-3.35" x2="-2.27" y2="-2.1" layer="51"/>
<rectangle x1="-0.23" y1="-3.35" x2="0.27" y2="-2.1" layer="51"/>
<rectangle x1="2.31" y1="-3.35" x2="2.81" y2="-2.1" layer="51"/>
<rectangle x1="2.27" y1="2.1" x2="2.77" y2="3.35" layer="51"/>
<rectangle x1="-0.27" y1="2.1" x2="0.23" y2="3.35" layer="51"/>
<rectangle x1="-2.81" y1="2.1" x2="-2.31" y2="3.35" layer="51"/>
</package>
</packages>
<packages3d>
<package3d name="DIL06" urn="urn:adsk.eagle:package:24361/1" type="box" library_version="1">
<description>Dual In Line Package</description>
<packageinstances>
<packageinstance name="DIL06"/>
</packageinstances>
</package3d>
<package3d name="DIL06SMD" urn="urn:adsk.eagle:package:24363/1" type="box" library_version="1">
<description>DIL06 SMD NAiS
Source: http://www.mew-europe.com/..  pti_en.pdf</description>
<packageinstances>
<packageinstance name="DIL06SMD"/>
</packageinstances>
</package3d>
<package3d name="SOP06" urn="urn:adsk.eagle:package:24367/1" type="box" library_version="1">
<description>SOP6 - AQV21, AQV22, AQV41 Sereis NAiSSource: http://www.mew-europe.com/..  pti_en.pdf</description>
<packageinstances>
<packageinstance name="SOP06"/>
</packageinstances>
</package3d>
</packages3d>
<symbols>
<symbol name="PHOTO-REKAY-2LED-2D1S" urn="urn:adsk.eagle:symbol:24036/1" library_version="1">
<wire x1="-5.08" y1="5.08" x2="-5.08" y2="-5.08" width="0.1524" layer="94"/>
<wire x1="3.302" y1="5.334" x2="3.302" y2="4.826" width="0.1524" layer="94"/>
<wire x1="3.302" y1="4.318" x2="3.302" y2="4.064" width="0.1524" layer="94"/>
<wire x1="3.302" y1="4.064" x2="3.302" y2="3.81" width="0.1524" layer="94"/>
<wire x1="3.302" y1="3.302" x2="3.302" y2="3.048" width="0.1524" layer="94"/>
<wire x1="3.302" y1="3.048" x2="3.302" y2="2.794" width="0.1524" layer="94"/>
<wire x1="3.302" y1="4.064" x2="4.064" y2="4.064" width="0.1524" layer="94"/>
<wire x1="3.302" y1="3.048" x2="4.064" y2="3.048" width="0.1524" layer="94"/>
<wire x1="4.064" y1="3.048" x2="4.064" y2="4.064" width="0.1524" layer="94"/>
<wire x1="2.794" y1="5.334" x2="2.794" y2="4.064" width="0.1524" layer="94"/>
<wire x1="2.794" y1="4.064" x2="2.794" y2="2.794" width="0.1524" layer="94"/>
<wire x1="2.794" y1="4.064" x2="2.032" y2="4.064" width="0.1524" layer="94"/>
<wire x1="3.302" y1="-5.334" x2="3.302" y2="-4.826" width="0.1524" layer="94"/>
<wire x1="3.302" y1="-4.318" x2="3.302" y2="-4.064" width="0.1524" layer="94"/>
<wire x1="3.302" y1="-4.064" x2="3.302" y2="-3.81" width="0.1524" layer="94"/>
<wire x1="3.302" y1="-3.302" x2="3.302" y2="-3.048" width="0.1524" layer="94"/>
<wire x1="3.302" y1="-3.048" x2="3.302" y2="-2.794" width="0.1524" layer="94"/>
<wire x1="3.302" y1="-4.064" x2="4.064" y2="-4.064" width="0.1524" layer="94"/>
<wire x1="3.302" y1="-3.048" x2="4.064" y2="-3.048" width="0.1524" layer="94"/>
<wire x1="4.064" y1="-3.048" x2="4.064" y2="-4.064" width="0.1524" layer="94"/>
<wire x1="4.064" y1="3.048" x2="4.064" y2="-3.048" width="0.1524" layer="94"/>
<wire x1="2.794" y1="-5.334" x2="2.794" y2="-4.064" width="0.1524" layer="94"/>
<wire x1="2.794" y1="-4.064" x2="2.794" y2="-2.794" width="0.1524" layer="94"/>
<wire x1="2.794" y1="-4.064" x2="2.032" y2="-4.064" width="0.1524" layer="94"/>
<wire x1="2.032" y1="4.064" x2="2.032" y2="-4.064" width="0.1524" layer="94"/>
<wire x1="-7.62" y1="7.62" x2="-7.62" y2="5.08" width="0.254" layer="94"/>
<wire x1="-7.62" y1="5.08" x2="-7.62" y2="-5.08" width="0.254" layer="94"/>
<wire x1="-7.62" y1="-5.08" x2="-7.62" y2="-7.62" width="0.254" layer="94"/>
<wire x1="-7.62" y1="-7.62" x2="7.62" y2="-7.62" width="0.254" layer="94"/>
<wire x1="7.62" y1="-7.62" x2="7.62" y2="-5.08" width="0.254" layer="94"/>
<wire x1="7.62" y1="-5.08" x2="7.62" y2="0" width="0.254" layer="94"/>
<wire x1="7.62" y1="0" x2="7.62" y2="5.08" width="0.254" layer="94"/>
<wire x1="7.62" y1="5.08" x2="7.62" y2="7.62" width="0.254" layer="94"/>
<wire x1="7.62" y1="7.62" x2="-7.62" y2="7.62" width="0.254" layer="94"/>
<wire x1="3.302" y1="5.08" x2="5.08" y2="5.08" width="0.1524" layer="94"/>
<wire x1="5.08" y1="5.08" x2="5.842" y2="5.08" width="0.1524" layer="94"/>
<wire x1="3.302" y1="-5.08" x2="5.842" y2="-5.08" width="0.1524" layer="94"/>
<wire x1="5.842" y1="5.08" x2="5.842" y2="-5.08" width="0.1524" layer="94"/>
<wire x1="4.064" y1="0" x2="5.08" y2="0" width="0.1524" layer="94"/>
<wire x1="-5.08" y1="5.08" x2="-7.62" y2="5.08" width="0.1524" layer="94"/>
<wire x1="-5.08" y1="-5.08" x2="-7.62" y2="-5.08" width="0.1524" layer="94"/>
<wire x1="7.62" y1="5.08" x2="5.08" y2="5.08" width="0.1524" layer="94"/>
<wire x1="7.62" y1="0" x2="5.08" y2="0" width="0.1524" layer="94"/>
<wire x1="7.62" y1="-5.08" x2="5.08" y2="-5.08" width="0.1524" layer="94"/>
<wire x1="-4.318" y1="0.508" x2="-2.032" y2="-0.762" width="0.2032" layer="94"/>
<wire x1="-2.032" y1="-0.762" x2="-2.032" y2="1.016" width="0.2032" layer="94"/>
<wire x1="-2.032" y1="1.016" x2="1.016" y2="-1.016" width="0.2032" layer="94"/>
<circle x="5.842" y="5.08" radius="0.127" width="0.254" layer="94"/>
<circle x="5.842" y="0" radius="0.127" width="0.254" layer="94"/>
<circle x="5.842" y="-5.08" radius="0.127" width="0.254" layer="94"/>
<text x="-7.62" y="8.89" size="1.778" layer="95" font="vector">&gt;NAME</text>
<text x="-7.62" y="-10.668" size="1.778" layer="96" font="vector">&gt;VALUE</text>
<rectangle x1="-6.35" y1="1.524" x2="-3.81" y2="1.778" layer="94"/>
<rectangle x1="5.334" y1="-4.445" x2="6.35" y2="-4.191" layer="94"/>
<rectangle x1="5.334" y1="4.191" x2="6.35" y2="4.445" layer="94"/>
<rectangle x1="-6.35" y1="-3.556" x2="-3.81" y2="-3.302" layer="94"/>
<pin name="K" x="-10.16" y="-5.08" visible="pad" length="short" direction="pas"/>
<pin name="D1" x="10.16" y="5.08" visible="pad" length="short" direction="pas" swaplevel="1" rot="R180"/>
<pin name="D2" x="10.16" y="-5.08" visible="pad" length="short" direction="pas" swaplevel="1" rot="R180"/>
<pin name="A" x="-10.16" y="5.08" visible="pad" length="short" direction="pas"/>
<pin name="S" x="10.16" y="0" visible="pad" length="short" direction="pas" rot="R180"/>
<polygon width="0.1524" layer="94">
<vertex x="-6.35" y="3.556"/>
<vertex x="-3.81" y="3.556"/>
<vertex x="-5.08" y="1.778"/>
</polygon>
<polygon width="0.1524" layer="94">
<vertex x="3.302" y="4.064"/>
<vertex x="3.81" y="4.318"/>
<vertex x="3.81" y="3.81"/>
</polygon>
<polygon width="0.1524" layer="94">
<vertex x="3.302" y="-4.064"/>
<vertex x="3.81" y="-3.81"/>
<vertex x="3.81" y="-4.318"/>
</polygon>
<polygon width="0.1524" layer="94">
<vertex x="5.842" y="4.191"/>
<vertex x="5.334" y="3.429"/>
<vertex x="6.35" y="3.429"/>
</polygon>
<polygon width="0.1524" layer="94">
<vertex x="5.842" y="-4.191"/>
<vertex x="6.35" y="-3.429"/>
<vertex x="5.334" y="-3.429"/>
</polygon>
<polygon width="0.1524" layer="94">
<vertex x="-6.35" y="-1.524"/>
<vertex x="-3.81" y="-1.524"/>
<vertex x="-5.08" y="-3.302"/>
</polygon>
<polygon width="0.1524" layer="94">
<vertex x="0" y="0.254"/>
<vertex x="-0.508" y="-0.508"/>
<vertex x="1.016" y="-1.016"/>
</polygon>
</symbol>
</symbols>
<devicesets>
<deviceset name="AQV*" urn="urn:adsk.eagle:component:24644/1" prefix="K" library_version="1">
<description>&lt;b&gt;PhotoMOS Relay&lt;/b&gt; NAiS&lt;p&gt;
Source: &lt;a href="http://www.panasonic-electric-works.com/catalogues/downloads/photomos/ds_x615_en_aqv10_20.pdf"&gt; Data sheet &lt;/a&gt;</description>
<gates>
<gate name="G$1" symbol="PHOTO-REKAY-2LED-2D1S" x="0" y="0"/>
</gates>
<devices>
<device name="" package="DIL06">
<connects>
<connect gate="G$1" pin="A" pad="1"/>
<connect gate="G$1" pin="D1" pad="6"/>
<connect gate="G$1" pin="D2" pad="4"/>
<connect gate="G$1" pin="K" pad="2"/>
<connect gate="G$1" pin="S" pad="5"/>
</connects>
<package3dinstances>
<package3dinstance package3d_urn="urn:adsk.eagle:package:24361/1"/>
</package3dinstances>
<technologies>
<technology name="10">
<attribute name="MF" value="AROMAT/ MATSUSHITA" constant="no"/>
<attribute name="MPN" value="AQV102" constant="no"/>
<attribute name="OC_FARNELL" value="2006029" constant="no"/>
<attribute name="OC_NEWARK" value="94F8718" constant="no"/>
</technology>
<technology name="20">
<attribute name="MF" value="AROMAT/ MATSUSHITA" constant="no"/>
<attribute name="MPN" value="AQV201" constant="no"/>
<attribute name="OC_FARNELL" value="1704180" constant="no"/>
<attribute name="OC_NEWARK" value="50F4048" constant="no"/>
</technology>
<technology name="21">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="AQV210" constant="no"/>
<attribute name="OC_FARNELL" value="1704179" constant="no"/>
<attribute name="OC_NEWARK" value="13P0968" constant="no"/>
</technology>
<technology name="22">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="1414197" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
<technology name="23">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
<technology name="234">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="AQV234" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="13P1031" constant="no"/>
</technology>
<technology name="25">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
<technology name="41">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
<technology name="45">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
</technologies>
</device>
<device name="SMD" package="DIL06SMD">
<connects>
<connect gate="G$1" pin="A" pad="1"/>
<connect gate="G$1" pin="D1" pad="6"/>
<connect gate="G$1" pin="D2" pad="4"/>
<connect gate="G$1" pin="K" pad="2"/>
<connect gate="G$1" pin="S" pad="5"/>
</connects>
<package3dinstances>
<package3dinstance package3d_urn="urn:adsk.eagle:package:24363/1"/>
</package3dinstances>
<technologies>
<technology name="21">
<attribute name="MF" value="AROMAT/ MATSUSHITA" constant="no"/>
<attribute name="MPN" value="AQV210S" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="95F6433" constant="no"/>
</technology>
<technology name="22">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
<technology name="23">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
<technology name="25">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
</technologies>
</device>
<device name="SOP" package="SOP06">
<connects>
<connect gate="G$1" pin="A" pad="1"/>
<connect gate="G$1" pin="D1" pad="6"/>
<connect gate="G$1" pin="D2" pad="4"/>
<connect gate="G$1" pin="K" pad="2"/>
<connect gate="G$1" pin="S" pad="5"/>
</connects>
<package3dinstances>
<package3dinstance package3d_urn="urn:adsk.eagle:package:24367/1"/>
</package3dinstances>
<technologies>
<technology name="21">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
<technology name="22">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
<technology name="41">
<attribute name="MF" value="" constant="no"/>
<attribute name="MPN" value="" constant="no"/>
<attribute name="OC_FARNELL" value="unknown" constant="no"/>
<attribute name="OC_NEWARK" value="unknown" constant="no"/>
</technology>
</technologies>
</device>
</devices>
</deviceset>
</devicesets>
</library>
<library name="SamacSys_Parts">
<description>&lt;b&gt;https://componentsearchengine.com&lt;/b&gt;&lt;p&gt;
&lt;author&gt;Created by SamacSys&lt;/author&gt;</description>
<packages>
<package name="DIP1330W46P254L1000H1375Q8N">
<description>&lt;b&gt;DIP AN&lt;/b&gt;&lt;br&gt;
</description>
<pad name="1" x="-6.65" y="3.81" drill="0.66" diameter="1.06" shape="square"/>
<pad name="2" x="-6.65" y="1.27" drill="0.66" diameter="1.06"/>
<pad name="3" x="-6.65" y="-1.27" drill="0.66" diameter="1.06"/>
<pad name="4" x="-6.65" y="-3.81" drill="0.66" diameter="1.06"/>
<pad name="5" x="6.65" y="-3.81" drill="0.66" diameter="1.06"/>
<pad name="6" x="6.65" y="-1.27" drill="0.66" diameter="1.06"/>
<pad name="7" x="6.65" y="1.27" drill="0.66" diameter="1.06"/>
<pad name="8" x="6.65" y="3.81" drill="0.66" diameter="1.06"/>
<text x="0" y="0" size="1.27" layer="25" align="center">&gt;NAME</text>
<text x="0" y="0" size="1.27" layer="27" align="center">&gt;VALUE</text>
<wire x1="-7.43" y1="5.25" x2="7.43" y2="5.25" width="0.05" layer="51"/>
<wire x1="7.43" y1="5.25" x2="7.43" y2="-5.25" width="0.05" layer="51"/>
<wire x1="7.43" y1="-5.25" x2="-7.43" y2="-5.25" width="0.05" layer="51"/>
<wire x1="-7.43" y1="-5.25" x2="-7.43" y2="5.25" width="0.05" layer="51"/>
<wire x1="-3.495" y1="5" x2="3.495" y2="5" width="0.1" layer="51"/>
<wire x1="3.495" y1="5" x2="3.495" y2="-5" width="0.1" layer="51"/>
<wire x1="3.495" y1="-5" x2="-3.495" y2="-5" width="0.1" layer="51"/>
<wire x1="-3.495" y1="-5" x2="-3.495" y2="5" width="0.1" layer="51"/>
<wire x1="-3.495" y1="3.73" x2="-2.225" y2="5" width="0.1" layer="51"/>
<wire x1="-7.18" y1="5" x2="3.495" y2="5" width="0.2" layer="21"/>
<wire x1="-3.495" y1="-5" x2="3.495" y2="-5" width="0.2" layer="21"/>
</package>
</packages>
<symbols>
<symbol name="SSCDANT030PG2A3">
<wire x1="5.08" y1="2.54" x2="27.94" y2="2.54" width="0.254" layer="94"/>
<wire x1="27.94" y1="-10.16" x2="27.94" y2="2.54" width="0.254" layer="94"/>
<wire x1="27.94" y1="-10.16" x2="5.08" y2="-10.16" width="0.254" layer="94"/>
<wire x1="5.08" y1="2.54" x2="5.08" y2="-10.16" width="0.254" layer="94"/>
<text x="29.21" y="7.62" size="1.778" layer="95" align="center-left">&gt;NAME</text>
<text x="29.21" y="5.08" size="1.778" layer="96" align="center-left">&gt;VALUE</text>
<pin name="GND" x="0" y="0" length="middle" direction="pwr"/>
<pin name="VSUPPLY" x="0" y="-2.54" length="middle" direction="pwr"/>
<pin name="SDA" x="0" y="-5.08" length="middle"/>
<pin name="SCL" x="0" y="-7.62" length="middle"/>
<pin name="NC_4" x="33.02" y="0" length="middle" rot="R180"/>
<pin name="NC_3" x="33.02" y="-2.54" length="middle" rot="R180"/>
<pin name="NC_2" x="33.02" y="-5.08" length="middle" rot="R180"/>
<pin name="NC_1" x="33.02" y="-7.62" length="middle" rot="R180"/>
</symbol>
</symbols>
<devicesets>
<deviceset name="SSCDANT030PG2A3" prefix="U">
<description>&lt;b&gt;Board Mount Pressure Sensors DIP,Single Ax Barbed Gage, 3.3V&lt;/b&gt;&lt;p&gt;
Source: &lt;a href="https://componentsearchengine.com/Datasheets/1/SSCDANT030PG2A3.pdf"&gt; Datasheet &lt;/a&gt;</description>
<gates>
<gate name="G$1" symbol="SSCDANT030PG2A3" x="0" y="0"/>
</gates>
<devices>
<device name="" package="DIP1330W46P254L1000H1375Q8N">
<connects>
<connect gate="G$1" pin="GND" pad="1"/>
<connect gate="G$1" pin="NC_1" pad="5"/>
<connect gate="G$1" pin="NC_2" pad="6"/>
<connect gate="G$1" pin="NC_3" pad="7"/>
<connect gate="G$1" pin="NC_4" pad="8"/>
<connect gate="G$1" pin="SCL" pad="4"/>
<connect gate="G$1" pin="SDA" pad="3"/>
<connect gate="G$1" pin="VSUPPLY" pad="2"/>
</connects>
<technologies>
<technology name="">
<attribute name="DESCRIPTION" value="Board Mount Pressure Sensors DIP,Single Ax Barbed Gage, 3.3V" constant="no"/>
<attribute name="HEIGHT" value="13.75mm" constant="no"/>
<attribute name="MANUFACTURER_NAME" value="Honeywell" constant="no"/>
<attribute name="MANUFACTURER_PART_NUMBER" value="SSCDANT030PG2A3" constant="no"/>
<attribute name="MOUSER_PART_NUMBER" value="" constant="no"/>
<attribute name="MOUSER_PRICE-STOCK" value="" constant="no"/>
<attribute name="RS_PART_NUMBER" value="" constant="no"/>
<attribute name="RS_PRICE-STOCK" value="" constant="no"/>
</technology>
</technologies>
</device>
</devices>
</deviceset>
</devicesets>
</library>
<library name="pinhead" urn="urn:adsk.eagle:library:325">
<description>&lt;b&gt;Pin Header Connectors&lt;/b&gt;&lt;p&gt;
&lt;author&gt;Created by librarian@cadsoft.de&lt;/author&gt;</description>
<packages>
<package name="2X10" urn="urn:adsk.eagle:footprint:22268/1" library_version="3">
<description>&lt;b&gt;PIN HEADER&lt;/b&gt;</description>
<wire x1="-12.7" y1="-1.905" x2="-12.065" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-10.795" y1="-2.54" x2="-10.16" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-10.16" y1="-1.905" x2="-9.525" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-8.255" y1="-2.54" x2="-7.62" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-7.62" y1="-1.905" x2="-6.985" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-5.715" y1="-2.54" x2="-5.08" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-5.08" y1="-1.905" x2="-4.445" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-3.175" y1="-2.54" x2="-2.54" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-2.54" y1="-1.905" x2="-1.905" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-0.635" y1="-2.54" x2="0" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="0" y1="-1.905" x2="0.635" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="1.905" y1="-2.54" x2="2.54" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-12.7" y1="-1.905" x2="-12.7" y2="1.905" width="0.1524" layer="21"/>
<wire x1="-12.7" y1="1.905" x2="-12.065" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-12.065" y1="2.54" x2="-10.795" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-10.795" y1="2.54" x2="-10.16" y2="1.905" width="0.1524" layer="21"/>
<wire x1="-10.16" y1="1.905" x2="-9.525" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-9.525" y1="2.54" x2="-8.255" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-8.255" y1="2.54" x2="-7.62" y2="1.905" width="0.1524" layer="21"/>
<wire x1="-7.62" y1="1.905" x2="-6.985" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-6.985" y1="2.54" x2="-5.715" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-5.715" y1="2.54" x2="-5.08" y2="1.905" width="0.1524" layer="21"/>
<wire x1="-5.08" y1="1.905" x2="-4.445" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-4.445" y1="2.54" x2="-3.175" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-3.175" y1="2.54" x2="-2.54" y2="1.905" width="0.1524" layer="21"/>
<wire x1="-2.54" y1="1.905" x2="-1.905" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-1.905" y1="2.54" x2="-0.635" y2="2.54" width="0.1524" layer="21"/>
<wire x1="-0.635" y1="2.54" x2="0" y2="1.905" width="0.1524" layer="21"/>
<wire x1="0" y1="1.905" x2="0.635" y2="2.54" width="0.1524" layer="21"/>
<wire x1="0.635" y1="2.54" x2="1.905" y2="2.54" width="0.1524" layer="21"/>
<wire x1="1.905" y1="2.54" x2="2.54" y2="1.905" width="0.1524" layer="21"/>
<wire x1="2.54" y1="1.905" x2="3.175" y2="2.54" width="0.1524" layer="21"/>
<wire x1="3.175" y1="2.54" x2="4.445" y2="2.54" width="0.1524" layer="21"/>
<wire x1="4.445" y1="2.54" x2="5.08" y2="1.905" width="0.1524" layer="21"/>
<wire x1="5.08" y1="1.905" x2="5.715" y2="2.54" width="0.1524" layer="21"/>
<wire x1="5.715" y1="2.54" x2="6.985" y2="2.54" width="0.1524" layer="21"/>
<wire x1="6.985" y1="2.54" x2="7.62" y2="1.905" width="0.1524" layer="21"/>
<wire x1="7.62" y1="1.905" x2="8.255" y2="2.54" width="0.1524" layer="21"/>
<wire x1="8.255" y1="2.54" x2="9.525" y2="2.54" width="0.1524" layer="21"/>
<wire x1="9.525" y1="2.54" x2="10.16" y2="1.905" width="0.1524" layer="21"/>
<wire x1="10.16" y1="-1.905" x2="9.525" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="7.62" y1="-1.905" x2="8.255" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="7.62" y1="-1.905" x2="6.985" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="5.08" y1="-1.905" x2="5.715" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="5.08" y1="-1.905" x2="4.445" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="2.54" y1="-1.905" x2="3.175" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-10.16" y1="1.905" x2="-10.16" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-7.62" y1="1.905" x2="-7.62" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-5.08" y1="1.905" x2="-5.08" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-2.54" y1="1.905" x2="-2.54" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="0" y1="1.905" x2="0" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="2.54" y1="1.905" x2="2.54" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="5.08" y1="1.905" x2="5.08" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="7.62" y1="1.905" x2="7.62" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="10.16" y1="1.905" x2="10.16" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="8.255" y1="-2.54" x2="9.525" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="5.715" y1="-2.54" x2="6.985" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="3.175" y1="-2.54" x2="4.445" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="0.635" y1="-2.54" x2="1.905" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-1.905" y1="-2.54" x2="-0.635" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-4.445" y1="-2.54" x2="-3.175" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-6.985" y1="-2.54" x2="-5.715" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-9.525" y1="-2.54" x2="-8.255" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="-12.065" y1="-2.54" x2="-10.795" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="10.16" y1="1.905" x2="10.795" y2="2.54" width="0.1524" layer="21"/>
<wire x1="10.795" y1="2.54" x2="12.065" y2="2.54" width="0.1524" layer="21"/>
<wire x1="12.065" y1="2.54" x2="12.7" y2="1.905" width="0.1524" layer="21"/>
<wire x1="12.7" y1="-1.905" x2="12.065" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="10.16" y1="-1.905" x2="10.795" y2="-2.54" width="0.1524" layer="21"/>
<wire x1="12.7" y1="1.905" x2="12.7" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="10.795" y1="-2.54" x2="12.065" y2="-2.54" width="0.1524" layer="21"/>
<pad name="1" x="-11.43" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="2" x="-11.43" y="1.27" drill="1.016" shape="octagon"/>
<pad name="3" x="-8.89" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="4" x="-8.89" y="1.27" drill="1.016" shape="octagon"/>
<pad name="5" x="-6.35" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="6" x="-6.35" y="1.27" drill="1.016" shape="octagon"/>
<pad name="7" x="-3.81" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="8" x="-3.81" y="1.27" drill="1.016" shape="octagon"/>
<pad name="9" x="-1.27" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="10" x="-1.27" y="1.27" drill="1.016" shape="octagon"/>
<pad name="11" x="1.27" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="12" x="1.27" y="1.27" drill="1.016" shape="octagon"/>
<pad name="13" x="3.81" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="14" x="3.81" y="1.27" drill="1.016" shape="octagon"/>
<pad name="15" x="6.35" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="16" x="6.35" y="1.27" drill="1.016" shape="octagon"/>
<pad name="17" x="8.89" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="18" x="8.89" y="1.27" drill="1.016" shape="octagon"/>
<pad name="19" x="11.43" y="-1.27" drill="1.016" shape="octagon"/>
<pad name="20" x="11.43" y="1.27" drill="1.016" shape="octagon"/>
<text x="-12.7" y="3.175" size="1.27" layer="25" ratio="10">&gt;NAME</text>
<text x="-12.7" y="-4.445" size="1.27" layer="27">&gt;VALUE</text>
<rectangle x1="-11.684" y1="-1.524" x2="-11.176" y2="-1.016" layer="51"/>
<rectangle x1="-11.684" y1="1.016" x2="-11.176" y2="1.524" layer="51"/>
<rectangle x1="-9.144" y1="1.016" x2="-8.636" y2="1.524" layer="51"/>
<rectangle x1="-9.144" y1="-1.524" x2="-8.636" y2="-1.016" layer="51"/>
<rectangle x1="-6.604" y1="1.016" x2="-6.096" y2="1.524" layer="51"/>
<rectangle x1="-6.604" y1="-1.524" x2="-6.096" y2="-1.016" layer="51"/>
<rectangle x1="-4.064" y1="1.016" x2="-3.556" y2="1.524" layer="51"/>
<rectangle x1="-1.524" y1="1.016" x2="-1.016" y2="1.524" layer="51"/>
<rectangle x1="1.016" y1="1.016" x2="1.524" y2="1.524" layer="51"/>
<rectangle x1="-4.064" y1="-1.524" x2="-3.556" y2="-1.016" layer="51"/>
<rectangle x1="-1.524" y1="-1.524" x2="-1.016" y2="-1.016" layer="51"/>
<rectangle x1="1.016" y1="-1.524" x2="1.524" y2="-1.016" layer="51"/>
<rectangle x1="3.556" y1="1.016" x2="4.064" y2="1.524" layer="51"/>
<rectangle x1="3.556" y1="-1.524" x2="4.064" y2="-1.016" layer="51"/>
<rectangle x1="6.096" y1="1.016" x2="6.604" y2="1.524" layer="51"/>
<rectangle x1="6.096" y1="-1.524" x2="6.604" y2="-1.016" layer="51"/>
<rectangle x1="8.636" y1="1.016" x2="9.144" y2="1.524" layer="51"/>
<rectangle x1="8.636" y1="-1.524" x2="9.144" y2="-1.016" layer="51"/>
<rectangle x1="11.176" y1="1.016" x2="11.684" y2="1.524" layer="51"/>
<rectangle x1="11.176" y1="-1.524" x2="11.684" y2="-1.016" layer="51"/>
</package>
<package name="2X10/90" urn="urn:adsk.eagle:footprint:22269/1" library_version="3">
<description>&lt;b&gt;PIN HEADER&lt;/b&gt;</description>
<wire x1="-12.7" y1="-1.905" x2="-10.16" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-10.16" y1="-1.905" x2="-10.16" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-10.16" y1="0.635" x2="-12.7" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-12.7" y1="0.635" x2="-12.7" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-11.43" y1="6.985" x2="-11.43" y2="1.27" width="0.762" layer="21"/>
<wire x1="-10.16" y1="-1.905" x2="-7.62" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-7.62" y1="-1.905" x2="-7.62" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-7.62" y1="0.635" x2="-10.16" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-8.89" y1="6.985" x2="-8.89" y2="1.27" width="0.762" layer="21"/>
<wire x1="-7.62" y1="-1.905" x2="-5.08" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-5.08" y1="-1.905" x2="-5.08" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-5.08" y1="0.635" x2="-7.62" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-6.35" y1="6.985" x2="-6.35" y2="1.27" width="0.762" layer="21"/>
<wire x1="-5.08" y1="-1.905" x2="-2.54" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-2.54" y1="-1.905" x2="-2.54" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-2.54" y1="0.635" x2="-5.08" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-3.81" y1="6.985" x2="-3.81" y2="1.27" width="0.762" layer="21"/>
<wire x1="-2.54" y1="-1.905" x2="0" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="0" y1="-1.905" x2="0" y2="0.635" width="0.1524" layer="21"/>
<wire x1="0" y1="0.635" x2="-2.54" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-1.27" y1="6.985" x2="-1.27" y2="1.27" width="0.762" layer="21"/>
<wire x1="0" y1="-1.905" x2="2.54" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="2.54" y1="-1.905" x2="2.54" y2="0.635" width="0.1524" layer="21"/>
<wire x1="2.54" y1="0.635" x2="0" y2="0.635" width="0.1524" layer="21"/>
<wire x1="1.27" y1="6.985" x2="1.27" y2="1.27" width="0.762" layer="21"/>
<wire x1="2.54" y1="-1.905" x2="5.08" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="5.08" y1="-1.905" x2="5.08" y2="0.635" width="0.1524" layer="21"/>
<wire x1="5.08" y1="0.635" x2="2.54" y2="0.635" width="0.1524" layer="21"/>
<wire x1="3.81" y1="6.985" x2="3.81" y2="1.27" width="0.762" layer="21"/>
<wire x1="5.08" y1="-1.905" x2="7.62" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="7.62" y1="-1.905" x2="7.62" y2="0.635" width="0.1524" layer="21"/>
<wire x1="7.62" y1="0.635" x2="5.08" y2="0.635" width="0.1524" layer="21"/>
<wire x1="6.35" y1="6.985" x2="6.35" y2="1.27" width="0.762" layer="21"/>
<wire x1="7.62" y1="-1.905" x2="10.16" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="10.16" y1="-1.905" x2="10.16" y2="0.635" width="0.1524" layer="21"/>
<wire x1="10.16" y1="0.635" x2="7.62" y2="0.635" width="0.1524" layer="21"/>
<wire x1="8.89" y1="6.985" x2="8.89" y2="1.27" width="0.762" layer="21"/>
<wire x1="10.16" y1="-1.905" x2="12.7" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="12.7" y1="-1.905" x2="12.7" y2="0.635" width="0.1524" layer="21"/>
<wire x1="12.7" y1="0.635" x2="10.16" y2="0.635" width="0.1524" layer="21"/>
<wire x1="11.43" y1="6.985" x2="11.43" y2="1.27" width="0.762" layer="21"/>
<pad name="2" x="-11.43" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="4" x="-8.89" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="6" x="-6.35" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="8" x="-3.81" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="10" x="-1.27" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="12" x="1.27" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="14" x="3.81" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="16" x="6.35" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="18" x="8.89" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="20" x="11.43" y="-3.81" drill="1.016" shape="octagon"/>
<pad name="1" x="-11.43" y="-6.35" drill="1.016" shape="octagon"/>
<pad name="3" x="-8.89" y="-6.35" drill="1.016" shape="octagon"/>
<pad name="5" x="-6.35" y="-6.35" drill="1.016" shape="octagon"/>
<pad name="7" x="-3.81" y="-6.35" drill="1.016" shape="octagon"/>
<pad name="9" x="-1.27" y="-6.35" drill="1.016" shape="octagon"/>
<pad name="11" x="1.27" y="-6.35" drill="1.016" shape="octagon"/>
<pad name="13" x="3.81" y="-6.35" drill="1.016" shape="octagon"/>
<pad name="15" x="6.35" y="-6.35" drill="1.016" shape="octagon"/>
<pad name="17" x="8.89" y="-6.35" drill="1.016" shape="octagon"/>
<pad name="19" x="11.43" y="-6.35" drill="1.016" shape="octagon"/>
<text x="-13.335" y="-3.81" size="1.27" layer="25" ratio="10" rot="R90">&gt;NAME</text>
<text x="14.605" y="-4.445" size="1.27" layer="27" rot="R90">&gt;VALUE</text>
<rectangle x1="-11.811" y1="0.635" x2="-11.049" y2="1.143" layer="21"/>
<rectangle x1="-9.271" y1="0.635" x2="-8.509" y2="1.143" layer="21"/>
<rectangle x1="-6.731" y1="0.635" x2="-5.969" y2="1.143" layer="21"/>
<rectangle x1="-4.191" y1="0.635" x2="-3.429" y2="1.143" layer="21"/>
<rectangle x1="-1.651" y1="0.635" x2="-0.889" y2="1.143" layer="21"/>
<rectangle x1="0.889" y1="0.635" x2="1.651" y2="1.143" layer="21"/>
<rectangle x1="3.429" y1="0.635" x2="4.191" y2="1.143" layer="21"/>
<rectangle x1="5.969" y1="0.635" x2="6.731" y2="1.143" layer="21"/>
<rectangle x1="8.509" y1="0.635" x2="9.271" y2="1.143" layer="21"/>
<rectangle x1="11.049" y1="0.635" x2="11.811" y2="1.143" layer="21"/>
<rectangle x1="-11.811" y1="-2.921" x2="-11.049" y2="-1.905" layer="21"/>
<rectangle x1="-9.271" y1="-2.921" x2="-8.509" y2="-1.905" layer="21"/>
<rectangle x1="-11.811" y1="-5.461" x2="-11.049" y2="-4.699" layer="21"/>
<rectangle x1="-11.811" y1="-4.699" x2="-11.049" y2="-2.921" layer="51"/>
<rectangle x1="-9.271" y1="-4.699" x2="-8.509" y2="-2.921" layer="51"/>
<rectangle x1="-9.271" y1="-5.461" x2="-8.509" y2="-4.699" layer="21"/>
<rectangle x1="-6.731" y1="-2.921" x2="-5.969" y2="-1.905" layer="21"/>
<rectangle x1="-4.191" y1="-2.921" x2="-3.429" y2="-1.905" layer="21"/>
<rectangle x1="-6.731" y1="-5.461" x2="-5.969" y2="-4.699" layer="21"/>
<rectangle x1="-6.731" y1="-4.699" x2="-5.969" y2="-2.921" layer="51"/>
<rectangle x1="-4.191" y1="-4.699" x2="-3.429" y2="-2.921" layer="51"/>
<rectangle x1="-4.191" y1="-5.461" x2="-3.429" y2="-4.699" layer="21"/>
<rectangle x1="-1.651" y1="-2.921" x2="-0.889" y2="-1.905" layer="21"/>
<rectangle x1="0.889" y1="-2.921" x2="1.651" y2="-1.905" layer="21"/>
<rectangle x1="-1.651" y1="-5.461" x2="-0.889" y2="-4.699" layer="21"/>
<rectangle x1="-1.651" y1="-4.699" x2="-0.889" y2="-2.921" layer="51"/>
<rectangle x1="0.889" y1="-4.699" x2="1.651" y2="-2.921" layer="51"/>
<rectangle x1="0.889" y1="-5.461" x2="1.651" y2="-4.699" layer="21"/>
<rectangle x1="3.429" y1="-2.921" x2="4.191" y2="-1.905" layer="21"/>
<rectangle x1="5.969" y1="-2.921" x2="6.731" y2="-1.905" layer="21"/>
<rectangle x1="3.429" y1="-5.461" x2="4.191" y2="-4.699" layer="21"/>
<rectangle x1="3.429" y1="-4.699" x2="4.191" y2="-2.921" layer="51"/>
<rectangle x1="5.969" y1="-4.699" x2="6.731" y2="-2.921" layer="51"/>
<rectangle x1="5.969" y1="-5.461" x2="6.731" y2="-4.699" layer="21"/>
<rectangle x1="8.509" y1="-2.921" x2="9.271" y2="-1.905" layer="21"/>
<rectangle x1="11.049" y1="-2.921" x2="11.811" y2="-1.905" layer="21"/>
<rectangle x1="8.509" y1="-5.461" x2="9.271" y2="-4.699" layer="21"/>
<rectangle x1="8.509" y1="-4.699" x2="9.271" y2="-2.921" layer="51"/>
<rectangle x1="11.049" y1="-4.699" x2="11.811" y2="-2.921" layer="51"/>
<rectangle x1="11.049" y1="-5.461" x2="11.811" y2="-4.699" layer="21"/>
</package>
<package name="1X02" urn="urn:adsk.eagle:footprint:22309/1" library_version="3">
<description>&lt;b&gt;PIN HEADER&lt;/b&gt;</description>
<wire x1="-1.905" y1="1.27" x2="-0.635" y2="1.27" width="0.1524" layer="21"/>
<wire x1="-0.635" y1="1.27" x2="0" y2="0.635" width="0.1524" layer="21"/>
<wire x1="0" y1="0.635" x2="0" y2="-0.635" width="0.1524" layer="21"/>
<wire x1="0" y1="-0.635" x2="-0.635" y2="-1.27" width="0.1524" layer="21"/>
<wire x1="-2.54" y1="0.635" x2="-2.54" y2="-0.635" width="0.1524" layer="21"/>
<wire x1="-1.905" y1="1.27" x2="-2.54" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-2.54" y1="-0.635" x2="-1.905" y2="-1.27" width="0.1524" layer="21"/>
<wire x1="-0.635" y1="-1.27" x2="-1.905" y2="-1.27" width="0.1524" layer="21"/>
<wire x1="0" y1="0.635" x2="0.635" y2="1.27" width="0.1524" layer="21"/>
<wire x1="0.635" y1="1.27" x2="1.905" y2="1.27" width="0.1524" layer="21"/>
<wire x1="1.905" y1="1.27" x2="2.54" y2="0.635" width="0.1524" layer="21"/>
<wire x1="2.54" y1="0.635" x2="2.54" y2="-0.635" width="0.1524" layer="21"/>
<wire x1="2.54" y1="-0.635" x2="1.905" y2="-1.27" width="0.1524" layer="21"/>
<wire x1="1.905" y1="-1.27" x2="0.635" y2="-1.27" width="0.1524" layer="21"/>
<wire x1="0.635" y1="-1.27" x2="0" y2="-0.635" width="0.1524" layer="21"/>
<pad name="1" x="-1.27" y="0" drill="1.016" shape="long" rot="R90"/>
<pad name="2" x="1.27" y="0" drill="1.016" shape="long" rot="R90"/>
<text x="-2.6162" y="1.8288" size="1.27" layer="25" ratio="10">&gt;NAME</text>
<text x="-2.54" y="-3.175" size="1.27" layer="27">&gt;VALUE</text>
<rectangle x1="-1.524" y1="-0.254" x2="-1.016" y2="0.254" layer="51"/>
<rectangle x1="1.016" y1="-0.254" x2="1.524" y2="0.254" layer="51"/>
</package>
<package name="1X02/90" urn="urn:adsk.eagle:footprint:22310/1" library_version="3">
<description>&lt;b&gt;PIN HEADER&lt;/b&gt;</description>
<wire x1="-2.54" y1="-1.905" x2="0" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="0" y1="-1.905" x2="0" y2="0.635" width="0.1524" layer="21"/>
<wire x1="0" y1="0.635" x2="-2.54" y2="0.635" width="0.1524" layer="21"/>
<wire x1="-2.54" y1="0.635" x2="-2.54" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="-1.27" y1="6.985" x2="-1.27" y2="1.27" width="0.762" layer="21"/>
<wire x1="0" y1="-1.905" x2="2.54" y2="-1.905" width="0.1524" layer="21"/>
<wire x1="2.54" y1="-1.905" x2="2.54" y2="0.635" width="0.1524" layer="21"/>
<wire x1="2.54" y1="0.635" x2="0" y2="0.635" width="0.1524" layer="21"/>
<wire x1="1.27" y1="6.985" x2="1.27" y2="1.27" width="0.762" layer="21"/>
<pad name="1" x="-1.27" y="-3.81" drill="1.016" shape="long" rot="R90"/>
<pad name="2" x="1.27" y="-3.81" drill="1.016" shape="long" rot="R90"/>
<text x="-3.175" y="-3.81" size="1.27" layer="25" ratio="10" rot="R90">&gt;NAME</text>
<text x="4.445" y="-3.81" size="1.27" layer="27" rot="R90">&gt;VALUE</text>
<rectangle x1="-1.651" y1="0.635" x2="-0.889" y2="1.143" layer="21"/>
<rectangle x1="0.889" y1="0.635" x2="1.651" y2="1.143" layer="21"/>
<rectangle x1="-1.651" y1="-2.921" x2="-0.889" y2="-1.905" layer="21"/>
<rectangle x1="0.889" y1="-2.921" x2="1.651" y2="-1.905" layer="21"/>
</package>
</packages>
<packages3d>
<package3d name="2X10" urn="urn:adsk.eagle:package:22405/2" type="model" library_version="3">
<description>PIN HEADER</description>
<packageinstances>
<packageinstance name="2X10"/>
</packageinstances>
</package3d>
<package3d name="2X10/90" urn="urn:adsk.eagle:package:22411/2" type="model" library_version="3">
<description>PIN HEADER</description>
<packageinstances>
<packageinstance name="2X10/90"/>
</packageinstances>
</package3d>
<package3d name="1X02" urn="urn:adsk.eagle:package:22435/2" type="model" library_version="3">
<description>PIN HEADER</description>
<packageinstances>
<packageinstance name="1X02"/>
</packageinstances>
</package3d>
<package3d name="1X02/90" urn="urn:adsk.eagle:package:22437/2" type="model" library_version="3">
<description>PIN HEADER</description>
<packageinstances>
<packageinstance name="1X02/90"/>
</packageinstances>
</package3d>
</packages3d>
<symbols>
<symbol name="PINH2X10" urn="urn:adsk.eagle:symbol:22266/1" library_version="3">
<wire x1="-6.35" y1="-15.24" x2="8.89" y2="-15.24" width="0.4064" layer="94"/>
<wire x1="8.89" y1="-15.24" x2="8.89" y2="12.7" width="0.4064" layer="94"/>
<wire x1="8.89" y1="12.7" x2="-6.35" y2="12.7" width="0.4064" layer="94"/>
<wire x1="-6.35" y1="12.7" x2="-6.35" y2="-15.24" width="0.4064" layer="94"/>
<text x="-6.35" y="13.335" size="1.778" layer="95">&gt;NAME</text>
<text x="-6.35" y="-17.78" size="1.778" layer="96">&gt;VALUE</text>
<pin name="1" x="-2.54" y="10.16" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="2" x="5.08" y="10.16" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
<pin name="3" x="-2.54" y="7.62" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="4" x="5.08" y="7.62" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
<pin name="5" x="-2.54" y="5.08" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="6" x="5.08" y="5.08" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
<pin name="7" x="-2.54" y="2.54" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="8" x="5.08" y="2.54" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
<pin name="9" x="-2.54" y="0" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="10" x="5.08" y="0" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
<pin name="11" x="-2.54" y="-2.54" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="12" x="5.08" y="-2.54" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
<pin name="13" x="-2.54" y="-5.08" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="14" x="5.08" y="-5.08" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
<pin name="15" x="-2.54" y="-7.62" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="16" x="5.08" y="-7.62" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
<pin name="17" x="-2.54" y="-10.16" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="18" x="5.08" y="-10.16" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
<pin name="19" x="-2.54" y="-12.7" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="20" x="5.08" y="-12.7" visible="pad" length="short" direction="pas" function="dot" rot="R180"/>
</symbol>
<symbol name="PINHD2" urn="urn:adsk.eagle:symbol:22308/1" library_version="3">
<wire x1="-6.35" y1="-2.54" x2="1.27" y2="-2.54" width="0.4064" layer="94"/>
<wire x1="1.27" y1="-2.54" x2="1.27" y2="5.08" width="0.4064" layer="94"/>
<wire x1="1.27" y1="5.08" x2="-6.35" y2="5.08" width="0.4064" layer="94"/>
<wire x1="-6.35" y1="5.08" x2="-6.35" y2="-2.54" width="0.4064" layer="94"/>
<text x="-6.35" y="5.715" size="1.778" layer="95">&gt;NAME</text>
<text x="-6.35" y="-5.08" size="1.778" layer="96">&gt;VALUE</text>
<pin name="1" x="-2.54" y="2.54" visible="pad" length="short" direction="pas" function="dot"/>
<pin name="2" x="-2.54" y="0" visible="pad" length="short" direction="pas" function="dot"/>
</symbol>
</symbols>
<devicesets>
<deviceset name="PINHD-2X10" urn="urn:adsk.eagle:component:22511/3" prefix="JP" uservalue="yes" library_version="3">
<description>&lt;b&gt;PIN HEADER&lt;/b&gt;</description>
<gates>
<gate name="A" symbol="PINH2X10" x="0" y="0"/>
</gates>
<devices>
<device name="" package="2X10">
<connects>
<connect gate="A" pin="1" pad="1"/>
<connect gate="A" pin="10" pad="10"/>
<connect gate="A" pin="11" pad="11"/>
<connect gate="A" pin="12" pad="12"/>
<connect gate="A" pin="13" pad="13"/>
<connect gate="A" pin="14" pad="14"/>
<connect gate="A" pin="15" pad="15"/>
<connect gate="A" pin="16" pad="16"/>
<connect gate="A" pin="17" pad="17"/>
<connect gate="A" pin="18" pad="18"/>
<connect gate="A" pin="19" pad="19"/>
<connect gate="A" pin="2" pad="2"/>
<connect gate="A" pin="20" pad="20"/>
<connect gate="A" pin="3" pad="3"/>
<connect gate="A" pin="4" pad="4"/>
<connect gate="A" pin="5" pad="5"/>
<connect gate="A" pin="6" pad="6"/>
<connect gate="A" pin="7" pad="7"/>
<connect gate="A" pin="8" pad="8"/>
<connect gate="A" pin="9" pad="9"/>
</connects>
<package3dinstances>
<package3dinstance package3d_urn="urn:adsk.eagle:package:22405/2"/>
</package3dinstances>
<technologies>
<technology name=""/>
</technologies>
</device>
<device name="/90" package="2X10/90">
<connects>
<connect gate="A" pin="1" pad="1"/>
<connect gate="A" pin="10" pad="10"/>
<connect gate="A" pin="11" pad="11"/>
<connect gate="A" pin="12" pad="12"/>
<connect gate="A" pin="13" pad="13"/>
<connect gate="A" pin="14" pad="14"/>
<connect gate="A" pin="15" pad="15"/>
<connect gate="A" pin="16" pad="16"/>
<connect gate="A" pin="17" pad="17"/>
<connect gate="A" pin="18" pad="18"/>
<connect gate="A" pin="19" pad="19"/>
<connect gate="A" pin="2" pad="2"/>
<connect gate="A" pin="20" pad="20"/>
<connect gate="A" pin="3" pad="3"/>
<connect gate="A" pin="4" pad="4"/>
<connect gate="A" pin="5" pad="5"/>
<connect gate="A" pin="6" pad="6"/>
<connect gate="A" pin="7" pad="7"/>
<connect gate="A" pin="8" pad="8"/>
<connect gate="A" pin="9" pad="9"/>
</connects>
<package3dinstances>
<package3dinstance package3d_urn="urn:adsk.eagle:package:22411/2"/>
</package3dinstances>
<technologies>
<technology name=""/>
</technologies>
</device>
</devices>
</deviceset>
<deviceset name="PINHD-1X2" urn="urn:adsk.eagle:component:22516/3" prefix="JP" uservalue="yes" library_version="3">
<description>&lt;b&gt;PIN HEADER&lt;/b&gt;</description>
<gates>
<gate name="G$1" symbol="PINHD2" x="0" y="0"/>
</gates>
<devices>
<device name="" package="1X02">
<connects>
<connect gate="G$1" pin="1" pad="1"/>
<connect gate="G$1" pin="2" pad="2"/>
</connects>
<package3dinstances>
<package3dinstance package3d_urn="urn:adsk.eagle:package:22435/2"/>
</package3dinstances>
<technologies>
<technology name=""/>
</technologies>
</device>
<device name="/90" package="1X02/90">
<connects>
<connect gate="G$1" pin="1" pad="1"/>
<connect gate="G$1" pin="2" pad="2"/>
</connects>
<package3dinstances>
<package3dinstance package3d_urn="urn:adsk.eagle:package:22437/2"/>
</package3dinstances>
<technologies>
<technology name=""/>
</technologies>
</device>
</devices>
</deviceset>
</devicesets>
</library>
</libraries>
<attributes>
</attributes>
<variantdefs>
</variantdefs>
<classes>
<class number="0" name="default" width="0" drill="0">
</class>
</classes>
<parts>
<part name="K1" library="relay" library_urn="urn:adsk.eagle:library:339" deviceset="AQV*" device="SMD" package3d_urn="urn:adsk.eagle:package:24363/1" technology="21"/>
<part name="K2" library="relay" library_urn="urn:adsk.eagle:library:339" deviceset="AQV*" device="SMD" package3d_urn="urn:adsk.eagle:package:24363/1" technology="21"/>
<part name="U1" library="SamacSys_Parts" deviceset="SSCDANT030PG2A3" device=""/>
<part name="J1" library="pinhead" library_urn="urn:adsk.eagle:library:325" deviceset="PINHD-2X10" device="" package3d_urn="urn:adsk.eagle:package:22405/2"/>
<part name="J5" library="pinhead" library_urn="urn:adsk.eagle:library:325" deviceset="PINHD-2X10" device="" package3d_urn="urn:adsk.eagle:package:22405/2"/>
<part name="JP1" library="pinhead" library_urn="urn:adsk.eagle:library:325" deviceset="PINHD-1X2" device="/90" package3d_urn="urn:adsk.eagle:package:22437/2" value="RelayPower"/>
<part name="JP2" library="pinhead" library_urn="urn:adsk.eagle:library:325" deviceset="PINHD-1X2" device="/90" package3d_urn="urn:adsk.eagle:package:22437/2" value="InflateRelay"/>
<part name="JP3" library="pinhead" library_urn="urn:adsk.eagle:library:325" deviceset="PINHD-1X2" device="/90" package3d_urn="urn:adsk.eagle:package:22437/2" value="DeflateRelay"/>
</parts>
<sheets>
<sheet>
<plain>
<text x="58.42" y="-22.86" size="1.778" layer="97">Used by LCD:
P6.0 - Y+
P6.1 - X+
P8.1 - X-
P8.2 - Y-
P2.5 - PWM
P3.7 - LCD reset
P3.2 - LCD_SCL
P2.7 - (LCD_SDC)</text>
</plain>
<instances>
<instance part="K1" gate="G$1" x="45.72" y="53.34" smashed="yes">
<attribute name="NAME" x="38.1" y="62.23" size="1.778" layer="95" font="vector"/>
<attribute name="VALUE" x="38.1" y="42.672" size="1.778" layer="96" font="vector"/>
</instance>
<instance part="K2" gate="G$1" x="114.3" y="53.34" smashed="yes">
<attribute name="NAME" x="106.68" y="62.23" size="1.778" layer="95" font="vector"/>
<attribute name="VALUE" x="106.68" y="42.672" size="1.778" layer="96" font="vector"/>
</instance>
<instance part="U1" gate="G$1" x="66.04" y="86.36" smashed="yes">
<attribute name="NAME" x="74.93" y="93.98" size="1.778" layer="95" align="center-left"/>
<attribute name="VALUE" x="74.93" y="91.44" size="1.778" layer="96" align="center-left"/>
</instance>
<instance part="J1" gate="A" x="35.56" y="15.24" smashed="yes">
<attribute name="NAME" x="29.21" y="28.575" size="1.778" layer="95"/>
<attribute name="VALUE" x="29.21" y="-2.54" size="1.778" layer="96"/>
</instance>
<instance part="J5" gate="A" x="88.9" y="15.24" smashed="yes">
<attribute name="NAME" x="82.55" y="28.575" size="1.778" layer="95"/>
<attribute name="VALUE" x="82.55" y="-2.54" size="1.778" layer="96"/>
</instance>
<instance part="JP1" gate="G$1" x="10.16" y="81.28" smashed="yes">
<attribute name="NAME" x="3.81" y="86.995" size="1.778" layer="95"/>
<attribute name="VALUE" x="3.81" y="76.2" size="1.778" layer="96"/>
</instance>
<instance part="JP2" gate="G$1" x="2.54" y="60.96" smashed="yes">
<attribute name="NAME" x="-3.81" y="66.675" size="1.778" layer="95"/>
<attribute name="VALUE" x="-3.81" y="55.88" size="1.778" layer="96"/>
</instance>
<instance part="JP3" gate="G$1" x="2.54" y="43.18" smashed="yes">
<attribute name="NAME" x="-3.81" y="48.895" size="1.778" layer="95"/>
<attribute name="VALUE" x="-3.81" y="38.1" size="1.778" layer="96"/>
</instance>
</instances>
<busses>
</busses>
<nets>
<net name="3V3" class="0">
<segment>
<pinref part="J1" gate="A" pin="1"/>
<wire x1="33.02" y1="25.4" x2="17.78" y2="25.4" width="0.1524" layer="91"/>
<label x="20.32" y="25.4" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="U1" gate="G$1" pin="VSUPPLY"/>
<wire x1="66.04" y1="83.82" x2="50.8" y2="83.82" width="0.1524" layer="91"/>
<label x="53.34" y="83.82" size="1.778" layer="95"/>
</segment>
</net>
<net name="5V" class="0">
<segment>
<pinref part="J1" gate="A" pin="2"/>
<wire x1="40.64" y1="25.4" x2="53.34" y2="25.4" width="0.1524" layer="91"/>
<label x="48.26" y="25.4" size="1.778" layer="95"/>
</segment>
</net>
<net name="GND" class="0">
<segment>
<pinref part="J1" gate="A" pin="4"/>
<wire x1="40.64" y1="22.86" x2="53.34" y2="22.86" width="0.1524" layer="91"/>
<label x="48.26" y="22.86" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="J5" gate="A" pin="2"/>
<wire x1="93.98" y1="25.4" x2="109.22" y2="25.4" width="0.1524" layer="91"/>
<label x="101.6" y="25.4" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="U1" gate="G$1" pin="GND"/>
<wire x1="66.04" y1="86.36" x2="50.8" y2="86.36" width="0.1524" layer="91"/>
<label x="53.34" y="86.36" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="JP1" gate="G$1" pin="2"/>
<wire x1="7.62" y1="81.28" x2="-7.62" y2="81.28" width="0.1524" layer="91"/>
<label x="-5.08" y="81.28" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="K1" gate="G$1" pin="K"/>
<wire x1="35.56" y1="48.26" x2="20.32" y2="48.26" width="0.1524" layer="91"/>
<label x="25.4" y="48.26" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="K2" gate="G$1" pin="K"/>
<wire x1="104.14" y1="48.26" x2="88.9" y2="48.26" width="0.1524" layer="91"/>
<label x="91.44" y="48.26" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="JP2" gate="G$1" pin="2"/>
<wire x1="0" y1="60.96" x2="-12.7" y2="60.96" width="0.1524" layer="91"/>
<label x="-12.7" y="60.96" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="JP3" gate="G$1" pin="2"/>
<wire x1="0" y1="43.18" x2="-12.7" y2="43.18" width="0.1524" layer="91"/>
<label x="-12.7" y="43.18" size="1.778" layer="95"/>
</segment>
</net>
<net name="P4.1" class="0">
<segment>
<pinref part="J1" gate="A" pin="19"/>
<wire x1="33.02" y1="2.54" x2="17.78" y2="2.54" width="0.1524" layer="91"/>
<label x="20.32" y="2.54" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="U1" gate="G$1" pin="SDA"/>
<wire x1="66.04" y1="81.28" x2="50.8" y2="81.28" width="0.1524" layer="91"/>
<label x="53.34" y="81.28" size="1.778" layer="95"/>
</segment>
</net>
<net name="P3.5" class="0">
<segment>
<pinref part="J1" gate="A" pin="20"/>
<wire x1="40.64" y1="2.54" x2="58.42" y2="2.54" width="0.1524" layer="91" style="dashdot"/>
<label x="48.26" y="2.54" size="1.778" layer="95"/>
</segment>
</net>
<net name="12V" class="0">
<segment>
<pinref part="JP1" gate="G$1" pin="1"/>
<wire x1="7.62" y1="83.82" x2="-7.62" y2="83.82" width="0.1524" layer="91"/>
<label x="-5.08" y="83.82" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="K2" gate="G$1" pin="D1"/>
<wire x1="124.46" y1="58.42" x2="132.08" y2="58.42" width="0.1524" layer="91"/>
<label x="127" y="58.42" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="K1" gate="G$1" pin="D1"/>
<wire x1="55.88" y1="58.42" x2="60.96" y2="58.42" width="0.1524" layer="91"/>
<label x="58.42" y="58.42" size="1.778" layer="95"/>
</segment>
</net>
<net name="P4.2" class="0">
<segment>
<pinref part="J1" gate="A" pin="17"/>
<wire x1="33.02" y1="5.08" x2="17.78" y2="5.08" width="0.1524" layer="91"/>
<label x="20.32" y="5.08" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="U1" gate="G$1" pin="SCL"/>
<wire x1="66.04" y1="78.74" x2="50.8" y2="78.74" width="0.1524" layer="91"/>
<label x="53.34" y="78.74" size="1.778" layer="95"/>
</segment>
</net>
<net name="P8.2" class="0">
<segment>
<pinref part="J5" gate="A" pin="19"/>
<wire x1="86.36" y1="2.54" x2="71.12" y2="2.54" width="0.1524" layer="91" style="dashdot"/>
<label x="73.66" y="2.54" size="1.778" layer="95"/>
</segment>
</net>
<net name="P8.1" class="0">
<segment>
<pinref part="J5" gate="A" pin="20"/>
<wire x1="93.98" y1="2.54" x2="106.68" y2="2.54" width="0.1524" layer="91" style="dashdot"/>
<label x="101.6" y="2.54" size="1.778" layer="95"/>
</segment>
</net>
<net name="P6.0" class="0">
<segment>
<pinref part="J1" gate="A" pin="6"/>
<wire x1="40.64" y1="20.32" x2="53.34" y2="20.32" width="0.1524" layer="91" style="dashdot"/>
<label x="48.26" y="20.32" size="1.778" layer="95"/>
</segment>
</net>
<net name="P6.1" class="0">
<segment>
<pinref part="J1" gate="A" pin="8"/>
<wire x1="40.64" y1="17.78" x2="53.34" y2="17.78" width="0.1524" layer="91" style="dashdot"/>
<label x="48.26" y="17.78" size="1.778" layer="95"/>
</segment>
</net>
<net name="P2.7" class="0">
<segment>
<pinref part="J1" gate="A" pin="15"/>
<wire x1="33.02" y1="7.62" x2="17.78" y2="7.62" width="0.1524" layer="91" style="dashdot"/>
<label x="20.32" y="7.62" size="1.778" layer="95"/>
</segment>
</net>
<net name="P3.2" class="0">
<segment>
<pinref part="J1" gate="A" pin="13"/>
<wire x1="33.02" y1="10.16" x2="17.78" y2="10.16" width="0.1524" layer="91" style="dashdot"/>
<label x="20.32" y="10.16" size="1.778" layer="95"/>
</segment>
</net>
<net name="P2.5" class="0">
<segment>
<pinref part="J5" gate="A" pin="1"/>
<wire x1="86.36" y1="25.4" x2="71.12" y2="25.4" width="0.1524" layer="91" style="dashdot"/>
<label x="73.66" y="25.4" size="1.778" layer="95"/>
</segment>
</net>
<net name="P1.5" class="0">
<segment>
<pinref part="J5" gate="A" pin="5"/>
<wire x1="86.36" y1="20.32" x2="71.12" y2="20.32" width="0.1524" layer="91"/>
<label x="73.66" y="20.32" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="K2" gate="G$1" pin="A"/>
<wire x1="104.14" y1="58.42" x2="88.9" y2="58.42" width="0.1524" layer="91"/>
<label x="91.44" y="58.42" size="1.778" layer="95"/>
</segment>
</net>
<net name="P1.4" class="0">
<segment>
<pinref part="J5" gate="A" pin="7"/>
<wire x1="86.36" y1="17.78" x2="71.12" y2="17.78" width="0.1524" layer="91"/>
<label x="73.66" y="17.78" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="K1" gate="G$1" pin="A"/>
<wire x1="35.56" y1="58.42" x2="20.32" y2="58.42" width="0.1524" layer="91"/>
<label x="25.4" y="58.42" size="1.778" layer="95"/>
</segment>
</net>
<net name="P3.7" class="0">
<segment>
<pinref part="J5" gate="A" pin="17"/>
<wire x1="86.36" y1="5.08" x2="71.12" y2="5.08" width="0.1524" layer="91" style="dashdot"/>
<label x="73.66" y="5.08" size="1.778" layer="95"/>
</segment>
</net>
<net name="INFLATE_PWR" class="0">
<segment>
<pinref part="JP2" gate="G$1" pin="1"/>
<wire x1="0" y1="63.5" x2="-12.7" y2="63.5" width="0.1524" layer="91"/>
<label x="-22.86" y="63.5" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="K1" gate="G$1" pin="D2"/>
<wire x1="55.88" y1="48.26" x2="60.96" y2="48.26" width="0.1524" layer="91"/>
<label x="58.42" y="48.26" size="1.778" layer="95"/>
</segment>
</net>
<net name="DEFLATE_PWR" class="0">
<segment>
<pinref part="JP3" gate="G$1" pin="1"/>
<wire x1="0" y1="45.72" x2="-12.7" y2="45.72" width="0.1524" layer="91"/>
<label x="-25.4" y="45.72" size="1.778" layer="95"/>
</segment>
<segment>
<pinref part="K2" gate="G$1" pin="D2"/>
<wire x1="124.46" y1="48.26" x2="134.62" y2="48.26" width="0.1524" layer="91"/>
<label x="127" y="48.26" size="1.778" layer="95"/>
</segment>
</net>
</nets>
</sheet>
</sheets>
<errors>
<approved hash="104,1,66.04,83.82,U1,VSUPPLY,3V3,,,"/>
<approved hash="106,1,40.64,25.4,5V,,,,,"/>
<approved hash="106,1,86.36,25.4,P2.5,,,,,"/>
<approved hash="106,1,33.02,7.62,P2.7,,,,,"/>
<approved hash="106,1,33.02,10.16,P3.2,,,,,"/>
<approved hash="106,1,40.64,2.54,P3.5,,,,,"/>
<approved hash="106,1,86.36,5.08,P3.7,,,,,"/>
<approved hash="106,1,40.64,20.32,P6.0,,,,,"/>
<approved hash="106,1,40.64,17.78,P6.1,,,,,"/>
<approved hash="106,1,93.98,2.54,P8.1,,,,,"/>
<approved hash="106,1,86.36,2.54,P8.2,,,,,"/>
<approved hash="113,1,36.7877,15.4661,J1,,,,,"/>
<approved hash="113,1,90.1277,15.4661,J5,,,,,"/>
</errors>
</schematic>
</drawing>
<compatibility>
<note version="6.3" minversion="6.2.2" severity="warning">
Since Version 6.2.2 text objects can contain more than one line,
which will not be processed correctly with this version.
</note>
<note version="8.2" severity="warning">
Since Version 8.2, EAGLE supports online libraries. The ids
of those online libraries will not be understood (or retained)
with this version.
</note>
<note version="8.3" severity="warning">
Since Version 8.3, EAGLE supports URNs for individual library
assets (packages, symbols, and devices). The URNs of those assets
will not be understood (or retained) with this version.
</note>
<note version="8.3" severity="warning">
Since Version 8.3, EAGLE supports the association of 3D packages
with devices in libraries, schematics, and board files. Those 3D
packages will not be understood (or retained) with this version.
</note>
</compatibility>
</eagle>
