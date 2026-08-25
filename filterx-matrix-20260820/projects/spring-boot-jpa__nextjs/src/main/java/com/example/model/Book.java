package com.example.model;
import jakarta.persistence.*;
import java.math.BigDecimal;
@Entity @Table(name="books") public class Book {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) private Long id;
 @Column(nullable=false) private String title; @Column(nullable=false) private String genre;
 @Column(nullable=false) private BigDecimal price; private String note;
 @Column(name="author_id",nullable=false) private Long authorId;
 @ManyToOne(fetch=FetchType.LAZY) @JoinColumn(name="author_id",insertable=false,updatable=false) private Author author;
 public Long getId(){return id;} public String getTitle(){return title;} public String getGenre(){return genre;}
 public BigDecimal getPrice(){return price;} public String getNote(){return note;} public Long getAuthorId(){return authorId;} public Author getAuthor(){return author;}
}
